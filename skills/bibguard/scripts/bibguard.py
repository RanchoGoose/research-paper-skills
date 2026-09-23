#!/usr/bin/env python3
"""
bibguard.py — 写 paper 时的引用总管:加引用、查引用、统一格式。

五个源分工(以 AMiner 为主,其余补它拿不到的细节):
  AMiner      -> 出处主源。CVPR 这类走 CMT 的会议不进 OpenReview、
                 proceedings 出版前也没有 DOI,只有它知道这篇中了。
                 --add 时也是作者与年份的主源(paper/info 给完整作者列表)
  arXiv API   -> title / authors / 日期。唯一权威的标题来源,能发现论文改名;
                 API 被 429 时 --add 改读 arxiv.org/abs 页的 citation_* 元数据
  OpenReview  -> ICLR / ICML / NeurIPS / COLM 录用状态与等级(这些会议不发 DOI,
                 Crossref 与 OpenAlex 都查不到)
  Crossref    -> 任何有 DOI 的,顺带把 DOI 带回来
  doi.org     -> 按 DOI 内容协商取回权威记录,不依赖出版商

用法:
  python3 bibguard.py references.bib                    # 全量核对 + 报告
  python3 bibguard.py references.bib --add "<标题>"      # 查证后生成并追加一条
  python3 bibguard.py references.bib --fix              # 出处/格式写回 .bib
  python3 bibguard.py references.bib --only k1,k2       # 只查指定 key
  python3 bibguard.py references.bib --refresh          # 忽略缓存重查
  python3 bibguard.py references.bib --uncited main.tex # 正文没引用的条目

退出码: 0 = 全部无需改动;1 = 有条目需要处理(可当投稿前 gate)。
缓存写在 <bib同目录>/.refcache.json,可安全重跑(API 有限流)。

守门原则:查不到的绝不写进 .bib。凭空造一条看起来很像真的引用,
正是这个工具存在要防的事。
"""
import argparse, difflib, json, os, re, shutil, socket, sys, time
import urllib.error, urllib.parse, urllib.request

UA = os.environ.get("BIBGUARD_UA", "bibguard/1.0 (+bibliography verification)")
MAILTO = os.environ.get("BIBGUARD_MAILTO", "")

HERE = os.path.dirname(os.path.abspath(__file__))
VENUES = json.load(open(os.path.join(HERE, 'venues.json'), encoding='utf-8'))
VENUES = {k: v for k, v in VENUES.items() if not k.startswith('_')}

# Bump when the cached record's shape changes, so old rows are re-queried
# instead of silently reporting fields they never had.
CACHE_V = 3

# 主会/正式出处白名单。注意 Crossref 的会议名常以年份开头
# ("2025 IEEE/CVF Conference on ... (CVPR)"),所以允许前导年份。
MAIN_VENUE = re.compile(
    r'^\s*(\d{4}\s+)?(ICLR|ICML|NeurIPS|NIPS|CVPR|ICCV|ECCV|ACL|EMNLP|NAACL|COLING|AAAI|'
    r'IJCAI|SIGGRAPH|UIST|HPCA|ISCA|MICRO|ASPLOS|OSDI|SOSP|NSDI|MLSys|COLM|WACV|BMVC|'
    r'IEEE|ACM|Proceedings|Advances\s+in\s+Neural|International\s+Conference|'
    r'Transactions\s+on|Journal\s+of|Nature|Science)\b', re.I)
# 明确不算发表的状态串(会触发 WORKSHOP_OR_REJECTED 告警)
NON_VENUE = re.compile(
    r'submitted\s+to|withdrawn|desk\s+reject|rejected|under\s+review', re.I)
# 明确是 workshop 的信号(即使以主会缩写开头也要排除,如 "ICML 2025 Workshop on X")
WORKSHOP = re.compile(r'workshop|\bWS\b', re.I)
# DBLP 镜像的 preprint 记录,既不是发表也不是拒稿,应完全忽略
CORR = re.compile(r'\bCoRR\b', re.I)


def norm(s):
    return ' '.join(re.sub(r'[^a-z0-9 ]', ' ', (s or '').lower()).split())


def sim(a, b):
    return difflib.SequenceMatcher(None, norm(a), norm(b)).ratio()


# Minimum seconds between two requests to the same host. A flat global --pause
# does not prevent 429s: with five sources per entry, arXiv still sees a request
# every ~10s early on and then rate-limits mid-sweep, and a 429 recorded as
# "checked, nothing found" is exactly how an unverified entry passes as clean.
# arXiv asks for >=3s; the rest are set from observed limits.
HOST_GAP = {
    'export.arxiv.org': 4.0,
    'arxiv.org': 4.0,
    'api2.openreview.net': 2.0,
    'api.crossref.org': 1.5,
    'datacenter.aminer.cn': 1.0,
    'doi.org': 1.0,
    'dblp.org': 2.0,
}
_LAST_HIT = {}
EXTRA_GAP = 0.0      # raised by --pause when a network needs to go slower still


def throttle(url):
    """Sleep just long enough that this host's minimum gap is respected."""
    host = urllib.parse.urlparse(url).netloc
    gap = HOST_GAP.get(host, 1.0) + EXTRA_GAP
    wait = _LAST_HIT.get(host, 0.0) + gap - time.monotonic()
    if wait > 0:
        time.sleep(wait)
    _LAST_HIT[host] = time.monotonic()


def backoff(exc, attempt, base):
    """Honour Retry-After when the server sends one, else exponential."""
    ra = None
    if isinstance(exc, urllib.error.HTTPError):
        try:
            ra = float(exc.headers.get('Retry-After') or 0)
        except (TypeError, ValueError):
            ra = None
    time.sleep(min(max(ra or base * (2 ** attempt), base), 90))


def http_json(url, tries=3, pause=6):
    req = urllib.request.Request(url, headers={'User-Agent': UA})
    for i in range(tries):
        throttle(url)
        try:
            with urllib.request.urlopen(req, timeout=40) as r:
                return json.loads(r.read().decode('utf-8', 'replace'))
        except Exception as e:
            if i == tries - 1:
                return {'__err': f'{type(e).__name__}: {str(e)[:60]}'}
            backoff(e, i, pause)


# ---------------------------------------------------------------- bib parsing
def split_fields(body):
    """按 depth-0 的逗号切字段(不能直接 split(','),字段值里有逗号)。"""
    out, cur, d = [], '', 0
    for ch in body:
        if ch == '{':
            d += 1
        elif ch == '}':
            d -= 1
        if ch == ',' and d == 0:
            out.append(cur); cur = ''
        else:
            cur += ch
    if cur.strip():
        out.append(cur)
    return out


def parse_bib(path):
    s = open(path, encoding='utf-8').read()
    # 只从第一个真条目开始,避开文件头注释(.bib 里 % 不是注释,但 @ 才起条目)
    entries = []
    for m in re.finditer(r'@(\w+)\{([^,]+),(.*?)\n\}', s, re.S):
        typ, key, body = m.group(1).lower(), m.group(2).strip(), m.group(3)
        f = {}
        for fld in split_fields(body):
            km = re.match(r'\s*(\w+)\s*=\s*(.*)', fld, re.S)
            if not km:
                continue
            f[km.group(1).lower()] = ' '.join(
                re.sub(r'^[{"]|[}"]$', '', km.group(2).strip()).split())
        if not f.get('title'):
            continue
        blob = ' '.join([f.get('journal', ''), f.get('note', ''), f.get('doi', '')])
        dm = re.search(r'\b(10\.\d{4,9}/[^\s;,}]+)', blob)
        # DOI 里的数字不是 arXiv id:doi:10.1109/cvpr52734.2025.00245 曾被读成
        # arXiv:2734.2025,--fix 还把它写进了 note。arXiv 自己的 DataCite DOI
        # (10.48550/arxiv.NNNN.NNNNN)除外,那里的数字就是 id。
        ax_blob = re.sub(r'\b10\.(?!48550/arxiv\.)\d{4,9}/[^\s;,}]+', ' ',
                         f.get('journal', '') + ' ' + f.get('note', ''), flags=re.I)
        am = re.search(r'(\d{4}\.\d{4,5})', ax_blob)
        entries.append(dict(
            key=key, type=typ, doi=dm.group(1) if dm else None,
            title=re.sub(r'[{}\\]', '', f['title']),
            year=f.get('year', '?'),
            current=f.get('booktitle') or f.get('journal') or '?',
            arxiv=am.group(1) if am else None,
        ))
    return entries


# ---------------------------------------------------------------- sources
def short_query(title):
    """OpenReview ranks badly on very long terms: sending a full 20-word title
    buries the real hit or returns empty notes. Query on the distinctive head of
    the title (up to the subtitle colon, capped), then still gate the *result*
    on full-title similarity so precision is unchanged.
    """
    head = title.split(':')[0].strip()
    if len(head.split()) < 4:
        head = title
    return ' '.join(head.split()[:12])


def q_openreview(title):
    d = {}
    for term in dict.fromkeys([short_query(title), title]):
        u = "https://api2.openreview.net/notes/search?" + urllib.parse.urlencode(
            {'term': term, 'limit': 12, 'type': 'terms'})
        d = http_json(u)
        if '__err' not in d and d.get('notes'):
            # keep querying only until something plausible comes back
            if any((n.get('content', {}) or {}).get('venue') for n in d['notes']):
                break
    if '__err' in d:
        return {'err': d['__err'], 'venues': []}
    v = []
    for n in d.get('notes', []):
        c = n.get('content', {})
        g = lambda k: (c.get(k, {}).get('value') if isinstance(c.get(k), dict) else c.get(k))
        ven, ti = g('venue'), g('title')
        if not ven or not ti or sim(title, ti) <= 0.80:
            continue
        v.append(str(ven))
    return {'err': None, 'venues': list(dict.fromkeys(v))}


def q_crossref(title):
    u = "https://api.crossref.org/works?" + urllib.parse.urlencode(
        {'query.bibliographic': title, 'rows': 4, 'mailto': MAILTO})
    d = http_json(u)
    if '__err' in d:
        return {'err': d['__err'], 'venues': []}
    v = []
    for w in d.get('message', {}).get('items', []):
        if sim(title, (w.get('title') or [''])[0]) < 0.80:
            continue
        ct = (w.get('container-title') or ['-'])[0]
        yr = (w.get('published', {}).get('date-parts') or [[None]])[0][0]
        v.append({'venue': ct, 'year': yr, 'doi': w.get('DOI'), 'type': w.get('type')})
    return {'err': None, 'venues': v}


def q_arxiv(entry):
    import xml.etree.ElementTree as ET
    NS = {'a': 'http://www.w3.org/2005/Atom'}
    if entry['arxiv']:
        u = "http://export.arxiv.org/api/query?id_list=%s" % entry['arxiv']
    else:
        u = "http://export.arxiv.org/api/query?" + urllib.parse.urlencode(
            {'search_query': 'ti:"%s"' % entry['title'], 'max_results': 3})
    root = None
    for i in range(4):                       # arXiv 会 429,必须退避重试
        throttle(u)
        try:
            with urllib.request.urlopen(urllib.request.Request(u, headers={'User-Agent': UA}),
                                        timeout=40) as r:
                root = ET.fromstring(r.read())
            break
        except Exception as e:
            if i == 3:
                return {'err': '%s:%s' % (type(e).__name__, str(e)[:40]),
                        'title': None, 'authors': None, 'jref': None,
                        'year': None, 'id': entry['arxiv']}
            backoff(e, i, 6)
    for e in root.findall('a:entry', NS):
        ti = ' '.join((e.find('a:title', NS).text or '').split())
        # With an id and no title yet (--add by arXiv id) the id *is* the match.
        if entry['title'] and sim(entry['title'], ti) < 0.80:
            continue
        jr = e.find('a:journal_ref', NS)
        pub = e.find('a:published', NS)
        idl = e.find('a:id', NS)
        aid = re.search(r'abs/(\d{4}\.\d{4,5})', idl.text) if idl is not None else None
        return {'err': None, 'title': ti,
                'authors': [a.find('a:name', NS).text for a in e.findall('a:author', NS)],
                'year': (pub.text or '')[:4] if pub is not None else None,
                'id': aid.group(1) if aid else entry['arxiv'],
                'jref': jr.text if jr is not None else None}
    # "Not on arXiv" is an answer, not a failure -- plenty of real papers never
    # get posted (journal-only, Nature, older proceedings). Caching that as an
    # error would re-query it forever. But when the bib *gave* an id and the
    # title still does not match, that is a genuine discrepancy worth surfacing.
    return {'err': 'no-title-match' if entry['arxiv'] else 'not-on-arxiv',
            'title': None, 'authors': None, 'jref': None,
            'year': None, 'id': entry['arxiv']}


def aminer_key():
    """Key from the environment, or from a file kept outside the repo.

    Never read it from inside the project: a bibliography lives in git and a
    key committed once stays in the history.
    """
    k = os.environ.get('AMINER_API_KEY', '').strip()
    if k:
        return k
    for p in (os.environ.get('AMINER_KEY_FILE'),
              os.path.expanduser('~/.claude/aminer_key'),
              os.path.expanduser('~/.aminer_key')):
        if p and os.path.exists(p):
            try:
                return open(p, encoding='utf-8').read().strip()
            except Exception:
                pass
    return ''


def q_aminer(title, key):
    """AMiner paper search -> venue name.

    Reachable from cloud egress where DBLP is not, and it indexes venues that
    Crossref and OpenReview between them still miss (notably Chinese-hosted
    proceedings). Everything goes in the query string: a JSON body returns
    "必填字段 title 不存在" and then silently answers an unrelated query.
    """
    if not key:
        return {'err': 'no-key', 'venues': []}
    u = ("https://datacenter.aminer.cn/gateway/open_platform/api/paper/search?"
         + urllib.parse.urlencode({'title': title, 'page': 0, 'size': 5}))
    req = urllib.request.Request(u, headers={
        'User-Agent': UA, 'X-Platform': 'openclaw',
        'Authorization': 'Bearer ' + key})
    d = None
    for i in range(3):
        throttle(u)
        try:
            with urllib.request.urlopen(req, timeout=40) as r:
                d = json.loads(r.read().decode('utf-8', 'replace'))
            break
        except Exception as e:
            if i == 2:
                return {'err': '%s:%s' % (type(e).__name__, str(e)[:40]), 'venues': []}
            backoff(e, i, 4)
    if not d or not d.get('success'):
        return {'err': 'aminer:%s' % str((d or {}).get('msg'))[:40], 'venues': []}
    v = []
    for it in (d.get('data') or []):
        if not isinstance(it, dict) or sim(title, it.get('title', '')) < 0.80:
            continue
        ven = it.get('venue_name')
        if ven:
            v.append({'venue': str(ven), 'year': it.get('year'),
                      'doi': it.get('doi'), 'type': 'proceedings-article'})
    return {'err': None, 'venues': v}


def aminer_info_parse(d):
    """paper/info response -> the fields --add needs, or None.

    The search endpoint names only the first author; the full author list, the
    year and the venue come from paper/info, whose ids go in a JSON body (the
    opposite of search). arXiv-only papers carry their DataCite DOI
    (10.48550/arxiv.NNNN.NNNNN), which is where the arXiv id comes from.
    """
    rows = (d or {}).get('data') or []
    if not (d or {}).get('success') or not rows or not isinstance(rows[0], dict):
        return None
    it = rows[0]
    names = [' '.join(str(a.get('name') or '').split())
             for a in (it.get('authors') or []) if isinstance(a, dict)]
    doi = str(it.get('doi') or '')
    m = re.search(r'10\.48550/arxiv\.(\d{4}\.\d{4,5})', doi, re.I)
    ven = it.get('venue')
    ven = ven.get('raw') if isinstance(ven, dict) else ven
    return {'id': it.get('id'), 'title': ' '.join(str(it.get('title') or '').split()),
            'authors': [n for n in names if n], 'year': str(it.get('year') or ''),
            'venue': ven or None, 'doi': doi or None,
            'arxiv': m.group(1) if m else None}


def aminer_queries(title):
    """Search strings to try, most specific first.

    AMiner's title search returns nothing for "A$^2$RD: Agentic ..." and also
    for its own stored "A^2RD: ..." spelling, yet finds the paper from the words
    after the colon. Every hit is still gated on the *full* title afterwards.
    """
    plain = ' '.join(re.sub(r'[$^{}\\]', '', title).split())
    tail = plain.split(':', 1)[1].strip() if ':' in plain else ''
    out = []
    for q in (title, plain, tail):
        if q and len(q.split()) >= 3 and q not in out:
            out.append(q)
    return out


def q_aminer_record(title, key):
    """AMiner as the source of the entry itself: title match, then full record.

    --add used to take authors and year from the arXiv API alone, so one 429
    there refused every arXiv-only paper although AMiner indexes them. The hit
    must match the title closely (>= 0.90): a near-miss would put the wrong
    authors on a real title, which is worse than refusing.
    """
    if not key or not title:
        return {'err': 'no-key' if not key else 'no-title'}
    hdr = {'User-Agent': UA, 'X-Platform': 'openclaw', 'Authorization': 'Bearer ' + key}
    hit = None
    for q in aminer_queries(title):
        u = ("https://datacenter.aminer.cn/gateway/open_platform/api/paper/search?"
             + urllib.parse.urlencode({'title': q, 'page': 0, 'size': 5}))
        for i in range(3):
            throttle(u)
            try:
                with urllib.request.urlopen(urllib.request.Request(u, headers=hdr),
                                            timeout=40) as r:
                    d = json.loads(r.read().decode('utf-8', 'replace'))
                hits = sorted((it for it in (d.get('data') or []) if isinstance(it, dict)),
                              key=lambda it: -sim(title, it.get('title', '')))
                if hits and sim(title, hits[0].get('title', '')) >= 0.90:
                    hit = hits[0]
                break
            except Exception as e:
                if i == 2:
                    return {'err': '%s:%s' % (type(e).__name__, str(e)[:40])}
                backoff(e, i, 4)
        if hit:
            break
    if not hit or not hit.get('id'):
        return {'err': 'aminer:no-title-match'}
    u2 = "https://datacenter.aminer.cn/gateway/open_platform/api/paper/info"
    body = json.dumps({'ids': [hit['id']]}).encode()
    rec = None
    for i in range(3):
        throttle(u2)
        try:
            req = urllib.request.Request(u2, data=body, method='POST', headers=dict(
                hdr, **{'Content-Type': 'application/json'}))
            with urllib.request.urlopen(req, timeout=60) as r:
                rec = aminer_info_parse(json.loads(r.read().decode('utf-8', 'replace')))
            break
        except Exception as e:
            if i == 2:
                return {'err': '%s:%s' % (type(e).__name__, str(e)[:40])}
            backoff(e, i, 4)
    if not rec or sim(title, rec['title']) < 0.90:
        return {'err': 'aminer:info-mismatch'}
    rec['err'] = None
    return rec


def arxiv_abs_parse(page):
    """citation_* meta tags of an arxiv.org/abs page -> title, authors, year."""
    import html
    def metas(name):
        return [html.unescape(m) for m in re.findall(
            r'<meta\s+name="%s"\s+content="([^"]*)"' % name, page or '')]
    ti, dt = metas('citation_title'), metas('citation_date')
    if not ti:
        return None
    return {'title': ' '.join(ti[0].split()),
            'authors': [' '.join(a.split()) for a in metas('citation_author')],
            'year': dt[0][:4] if dt else None}


def q_arxiv_abs(aid):
    """The arxiv.org/abs page, for when the export API answers 429.

    The two are rate-limited separately (2026-09-15: the API returned 429 while
    abs pages returned 200), and the page carries the same title and date.
    """
    u = "https://arxiv.org/abs/%s" % aid
    miss = {'title': None, 'authors': None, 'year': None, 'id': aid, 'jref': None}
    throttle(u)
    try:
        with urllib.request.urlopen(urllib.request.Request(u, headers={'User-Agent': UA}),
                                    timeout=40) as r:
            got = arxiv_abs_parse(r.read().decode('utf-8', 'replace'))
    except Exception as e:
        return dict(miss, err='%s:%s' % (type(e).__name__, str(e)[:40]))
    if not got:
        return dict(miss, err='abs:no-meta')
    got.update(err=None, id=aid, jref=None)
    return got


def fix_caret(title):
    """AMiner flattens A$^2$RD to A^2RD, and a bare ^ breaks LaTeX in a title."""
    if '$' in title:
        return title
    return re.sub(r'\^(\{[^}]*\}|\w)', lambda m: '$^%s$' % m.group(1), title)


def csl_authors_year(d):
    """doi.org CSL-JSON -> (["Family, Given", ...], "YYYY" or None)."""
    au = []
    for a in (d or {}).get('author') or []:
        if a.get('literal'):
            au.append(a['literal'])
        elif a.get('family'):
            au.append('%s, %s' % (a['family'], a['given']) if a.get('given') else a['family'])
    parts = ((d or {}).get('issued') or {}).get('date-parts') or [[None]]
    y = parts[0][0] if parts and parts[0] else None
    return au, (str(y) if y else None)


def dblp_reachable(timeout=6):
    """DBLP is a 4th cross-check, but it refuses most cloud egress IPs.

    Measured on an AWS box (2026-08-11): DNS resolves and the TCP handshake to
    dblp.org:443 completes, then the request is reset one RTT later -- i.e. the
    far end rejects us, not a local middlebox. All three hostnames behave the
    same while other hosts in the same datacenter answer 200. So probe once and
    fall through quietly rather than burning a timeout on every entry.
    """
    try:
        with urllib.request.urlopen(urllib.request.Request(
                "https://dblp.org/search/publ/api?q=test&format=json",
                headers={'User-Agent': UA}), timeout=timeout) as r:
            return r.status == 200
    except Exception:
        return False


def q_doi(doi, title):
    """Resolve a DOI through doi.org content negotiation.

    This is the anchor that does not depend on arXiv or OpenReview: every
    registered DOI resolves here regardless of publisher (Crossref, DataCite,
    mEDRA...), and it returns the authoritative title/venue/authors. It is the
    only independent check available for a paper that was never posted to
    arXiv and never went through OpenReview.
    """
    if not doi:
        return {'err': 'no-doi', 'ok': False, 'title': None, 'venue': None}
    u = "https://doi.org/" + urllib.parse.quote(doi, safe='/:')
    req = urllib.request.Request(u, headers={
        'User-Agent': UA, 'Accept': 'application/vnd.citationstyles.csl+json'})
    throttle(u)
    try:
        with urllib.request.urlopen(req, timeout=40) as r:
            d = json.loads(r.read().decode('utf-8', 'replace'))
    except Exception as e:
        return {'err': '%s:%s' % (type(e).__name__, str(e)[:40]),
                'ok': False, 'title': None, 'venue': None, 'authors': None, 'year': None}
    ti = d.get('title')
    ti = ti[0] if isinstance(ti, list) and ti else ti
    ven = d.get('container-title')
    ven = ven[0] if isinstance(ven, list) and ven else ven
    au, yr = csl_authors_year(d)
    # --add by DOI passes no title: the DOI itself is the match, as with an arXiv id.
    return {'err': None, 'ok': bool(ti) and (not title or sim(title, ti) >= 0.80),
            'title': ti, 'venue': ven, 'authors': au or None, 'year': yr}


def q_dblp(title):
    u = "https://dblp.org/search/publ/api?" + urllib.parse.urlencode(
        {'q': title, 'format': 'json', 'h': 8})
    d = http_json(u, tries=1)
    if '__err' in d:
        return {'err': d['__err'], 'venues': []}
    v = []
    for h in (d.get('result', {}).get('hits', {}).get('hit') or []):
        info = h.get('info', {})
        if sim(title, info.get('title', '')) < 0.80:
            continue
        ven, yr = info.get('venue'), info.get('year')
        if not ven or str(ven).lower() == 'corr':
            continue
        v.append({'venue': str(ven), 'year': yr, 'doi': info.get('doi'),
                  'type': 'proceedings-article'})
    return {'err': None, 'venues': v}


# ---------------------------------------------------------------- formatting
def canon_venue(text):
    """Map any venue string onto the canonical (kind, booktitle) pair."""
    t = norm(text)
    best = None
    for abbr, spec in VENUES.items():
        for pat in spec['match']:
            if pat in t:
                # longest match wins, so "naacl" beats a bare "acl" substring
                if best is None or len(pat) > best[0]:
                    best = (len(pat), abbr, spec)
    return (best[1], best[2]) if best else (None, None)


def field_re(name):
    return re.compile(r'(^\s*%s\s*=\s*)(\{.*?\}|"[^"]*"|[^,\n]*)(,?\s*$)'
                      % name, re.M | re.S)


def set_field(body, name, value, after=None):
    """Replace a field if present, else insert it (after `after` when given)."""
    m = field_re(name).search(body)
    if m:
        return body[:m.start()] + '  %s = {%s}%s' % (name, value, m.group(3)) + body[m.end():]
    anchor = field_re(after).search(body) if after else None
    ins = '\n  %s = {%s},' % (name, value)
    if anchor:
        return body[:anchor.end()] + ins + body[anchor.end():]
    return body.rstrip().rstrip(',') + ',' + ins + '\n'


def drop_field(body, name):
    m = field_re(name).search(body)
    return body[:m.start()] + body[m.end():] if m else body


def get_field(body, name):
    m = field_re(name).search(body)
    if not m:
        return None
    return ' '.join(re.sub(r'^[{"]|[}"]$', '', m.group(2).strip()).split())


def merge_note(old, new):
    """Union the two notes, keeping order and never dropping what was there.

    The existing note is hand-curated and can carry things no API returns --
    "spotlight", "oral", a correction, a caveat. Overwriting it silently loses
    them, so add only the tokens that are genuinely absent.
    """
    def ident(tok):                       # compare on the id, not the prefix
        m = re.search(r'(10\.\d{4,9}/\S+|\d{4}\.\d{4,5})', tok)
        return m.group(1).lower() if m else norm(tok)
    toks = [t.strip() for t in (old or '').split(';') if t.strip()]
    have = {ident(t) for t in toks}
    for t in [x.strip() for x in (new or '').split(';') if x.strip()]:
        if ident(t) not in have:
            toks.append(t); have.add(ident(t))
    return '; '.join(toks)


# ---------------------------------------------------------------- classify
def or_refused(or_venues):
    """OpenReview 记为撤稿/拒稿/在投的 (venue 缩写, 年份) 集合。

    实测 StreamingT2V:OpenReview 上是 "ICLR 2025 Conference Withdrawn Submission",
    AMiner 却给了一条光秃秃的 "ICLR 2025"(还挂着 CVPR 的 DOI)。AMiner 排第一,
    --add 就写成了 ICLR,--fix 又把已写的 ICLR 当成对的,真正的出处 CVPR 2025
    永远上不来。ICLR/ICML/NeurIPS 的录用结果以 OpenReview 为准:它说这一届
    撤了/拒了,别的源再说"中了"也不算 —— 除非 OpenReview 自己同一届也有录用记录。
    workshop 记录不算:workshop 撤稿说明不了主会。
    返回 (缩写, 年份, 缺年份时是否也算同届);OpenReview 在这个会有任何一届的
    录用记录时,缺年份的一方不能拿来否定(可能正是录用的那一届)。
    """
    bad, ok = set(), set()
    for v in or_venues:
        if CORR.search(v) or WORKSHOP.search(v):
            continue
        ab, _ = canon_venue(v)
        if ab:
            (bad if NON_VENUE.search(v) else ok).add((ab, venue_year(v, None)))
    took = {ab for ab, _ in ok}
    return {(ab, y, ab not in took) for ab, y in bad - ok}


def or_evidence(ev):
    """证据列表里 OpenReview 那几条的 venue 串(缓存行只存了证据,没存原始返回)。"""
    return [x[3:] for x in (ev or []) if x.startswith('OR:')]


def venue_year(venue, year):
    """年份:源给了就用,否则从 venue 串里取("ICLR 2025" 的 year 字段常是 None)。"""
    if str(year).isdigit():
        return int(year)
    m = re.search(r'\b((?:19|20)\d{2})\b', venue or '')
    return int(m.group(1)) if m else None


def refused(venue, year, bad):
    """这个 venue 是不是 OpenReview 说撤/拒了的那一届?bad 来自 or_refused。"""
    ab, _ = canon_venue(venue or '')
    y = venue_year(venue, year)
    return bool(ab) and any(b == ab and (by == y or (wild and (by is None or y is None)))
                            for b, by, wild in bad)


def classify(orv, cr, dbl=None, am=None):
    """返回 (状态, 建议 venue, 证据列表)。

    判定顺序很重要:
      1. 只要有**任何一个**正式主会/期刊出处 -> PUBLISHED。
         (很多正会论文同时挂着 workshop 记录或后续投稿的拒稿记录,
          不能因为看到"拒/撤/workshop"字样就否定它。)
      2. 否则,若有明确的 workshop / 拒稿 / 投稿中记录 -> WORKSHOP_OR_REJECTED。
      3. 否则 -> PREPRINT。
    CoRR(DBLP 镜像的 preprint 记录)全程忽略,它既不是发表也不是拒稿。

    AMiner 排在建议列表最前:它的覆盖面最广(CMT 系会议如 CVPR 既不进
    OpenReview 也在 proceedings 出版前没有 DOI,只有它看得见)。排序只决定
    "选哪个 venue",不决定细节 —— DOI 和录用等级仍从其他源回填。
    """
    ev, main, weak = [], [], False
    for v in orv['venues']:
        if CORR.search(v):
            continue
        ev.append('OR:' + v)
        if NON_VENUE.search(v) or WORKSHOP.search(v):
            weak = True
            continue
        if MAIN_VENUE.match(v):
            main.append(('openreview', v))
        else:
            weak = True          # 非白名单的 venue 串,多半是 workshop 简称
    bad = or_refused(orv['venues'])
    for src, w in ([('AMINER', x) for x in (am or {}).get('venues', [])]
                   + [('CR', x) for x in cr['venues']]
                   + [('DBLP', x) for x in (dbl or {}).get('venues', [])]):
        if CORR.search(w['venue']):
            continue
        ev.append("%s:%s (%s) [%s]" % (src, w['venue'], w['year'], w['type']))
        if w['type'] not in ('proceedings-article', 'journal-article', 'book-chapter'):
            continue
        if NON_VENUE.search(w['venue']) or WORKSHOP.search(w['venue']):
            weak = True
            continue
        if refused(w['venue'], w['year'], bad):
            continue             # OpenReview 说这一届撤/拒了(weak 已由那条记录置上)
        if MAIN_VENUE.match(w['venue']):
            main.append((src.lower(), "%s|%s|doi:%s" % (w['venue'], w['year'], w['doi'])))
    if main:
        # AMiner first, then the rest in their existing order (stable sort).
        main.sort(key=lambda t: t[0] != 'aminer')
        return 'PUBLISHED', main, ev
    if weak:
        return 'WORKSHOP_OR_REJECTED', [], ev
    return 'PREPRINT', [], ev


# Acceptance grade as OpenReview words it; harvested even when AMiner picks the
# venue, because AMiner records the venue but not the decision.
GRADE = re.compile(r'\b(oral|spotlight|poster|notable[- ]top[- ]\d+%?|highlight)\b', re.I)


def pick_venue(suggest, bib_year, arxiv_id):
    """Choose the venue to write into the .bib, and gather its details.

    AMiner is the primary decider (see classify); within one source the record
    whose year matches the .bib wins, else the earliest -- a paper cited as the
    2024 conference version must not be silently re-pointed at a 2026 reprint.

    The DOI and the acceptance grade are then harvested from *any* source that
    agrees on the same canonical venue, so preferring AMiner never costs us the
    DOI that only Crossref has or the "Oral" that only OpenReview has.
    """
    cands = []
    for i, (src, v) in enumerate(suggest):
        head = v.split('|')[0]
        ab, sp = canon_venue(head)
        if not ab:
            continue
        ym = re.search(r'\|(\d{4})\|', v) or re.search(r'\b(20\d{2})\b', head)
        cands.append({'src': src, 'ab': ab, 'sp': sp, 'raw': v, 'ord': i,
                      'year': int(ym.group(1)) if ym else None})
    if not cands:
        return None
    by = int(bib_year) if str(bib_year).isdigit() else None
    cands.sort(key=lambda c: (c['src'] != 'aminer',
                              c['year'] != by if by and c['year'] else True,
                              c['year'] or 9999,
                              c['ord']))
    win = cands[0]
    act = {'kind': win['sp']['kind'], 'book': win['sp']['book']}
    if win['year']:
        act['year'] = str(win['year'])
    # Same venue per anyone else? Take their DOI and their acceptance grade.
    agree = [c for c in cands if c['ab'] == win['ab']]
    doi = next((m.group(1) for c in agree
                for m in [re.search(r'doi:(\S+)', c['raw'])]
                if m and m.group(1) != 'None'), None)
    grade = next((m.group(1) for c in agree if c['src'] == 'openreview'
                  for m in [GRADE.search(c['raw'])] if m), None)
    bits = [grade, ('doi:' + doi) if doi else None,
            ('arXiv:' + arxiv_id) if arxiv_id else None]
    note = '; '.join(b for b in bits if b)
    if note:
        act['note'] = note
    return act


def tidy(body):
    """Remove the blank lines a dropped field leaves behind, and the trailing
    comma before the closing brace. Cosmetic, but the .bib is read by humans."""
    body = re.sub(r'\n[ \t]*\n+', '\n', body)
    return body.rstrip().rstrip(',')


def apply_fixes(bib_path, plan):
    """Rewrite the .bib in place: canonical venue, entry type, title, note.

    Edits are textual and per-entry so hand-written formatting, comments and
    field order all survive; only the fields we decided to change are touched.
    A .bak copy is written first.
    """
    src = open(bib_path, encoding='utf-8').read()
    out, changed = src, []
    for key, act in plan.items():
        m = re.search(r'@(\w+)\{%s,(.*?)\n\}' % re.escape(key), out, re.S)
        if not m:
            continue
        typ, body, new = m.group(1), m.group(2), m.group(2)
        newtyp = typ
        if act.get('title'):
            new = set_field(new, 'title', act['title'])
        if act.get('book'):
            kind, book = act['kind'], act['book']
            newtyp = 'inproceedings' if kind == 'conf' else 'article'
            new = drop_field(new, 'booktitle' if kind == 'jour' else 'journal')
            new = set_field(new, 'booktitle' if kind == 'conf' else 'journal',
                            book, after='author')
            if act.get('year'):
                new = set_field(new, 'year', act['year'])
            merged = merge_note(get_field(new, 'note'), act.get('note'))
            if merged:
                new = set_field(new, 'note', merged)
        if new != body or newtyp != typ:
            new = tidy(new)
            out = out[:m.start()] + '@%s{%s,%s\n}' % (newtyp, key, new) + out[m.end():]
            changed.append(key)
    if changed:
        shutil.copyfile(bib_path, bib_path + '.bak')
        open(bib_path, 'w', encoding='utf-8').write(out)
    return changed


# ---------------------------------------------------------------- add entry
def bib_author(name):
    """arXiv gives "Xun Huang"; BibTeX wants "Huang, Xun".

    Left alone if it already has a comma. Lowercase particles stay with the
    surname ("van den Berg, Rianne"), which is the usual BibTeX convention.
    """
    name = ' '.join((name or '').split())
    if not name or ',' in name:
        return name
    parts = name.split()
    if len(parts) == 1:
        return name
    cut = len(parts) - 1
    while cut > 1 and parts[cut - 1][:1].islower():
        cut -= 1
    return '%s, %s' % (' '.join(parts[cut:]), ' '.join(parts[:cut]))


def protect_caps(title):
    """Brace tokens BibTeX would otherwise lowercase: acronyms and CamelCase.

    Without this a .bst with a lowercasing title style renders "MuKV" as
    "Mukv" and "KV" as "Kv". Matches how the rest of the bibliography is
    written, so a generated entry is indistinguishable from a hand-written one.
    """
    def odd(seg):
        # >=2 capitals (KV, IEEE, NVFP4) or an inner capital (MuKV, LongLive)
        return len(seg) > 1 and (sum(c.isupper() for c in seg) >= 2
                                 or seg[1:] != seg[1:].lower())

    def one(tok):
        core = tok.strip('.,:;?!()[]')
        if len(core) < 2 or core.startswith('{'):
            return tok
        # Split on hyphen and slash first: "Multi-Grained" and "Train-Test" are
        # ordinary title case, not acronyms, and bracing them just adds noise.
        if any(odd(seg) for seg in re.split(r'[-/]', core)):
            return tok.replace(core, '{%s}' % core, 1)
        return tok
    return ' '.join(one(t) for t in title.split())


# "Gemma Team" is one author, not "Team, Gemma"; its report lists hundreds of
# people after it, and the citable author is the team.
CORP_AUTHOR = re.compile(r'\s+(Team|Consortium|Collaboration)$')


def make_key(title, year, taken, authors=None):
    """Key in the same shape the rest of the bibliography uses.

    Papers with a short name before the colon get that name plus the year --
    selfforcing2025, mukv2026, tethercache2026. Titles with no such name fall
    back to the other standard convention, first author surname plus year
    (vaswani2017), because slicing a long title mid-word produces keys like
    "attentionisallyounee2017".
    """
    head = title.split(':')[0].strip()
    slug = ''
    if ':' in title and len(head.split()) <= 4:
        slug = re.sub(r'[^a-z0-9]', '', head.lower())
    if not slug and authors:
        first = ' '.join(str(authors[0]).split())
        corp = CORP_AUTHOR.search(first)
        slug = re.sub(r'[^a-z0-9]', '', (first[:corp.start()] if corp else
                                         bib_author(first).split(',')[0]).lower())
    if not slug:                       # no colon, no authors: first two words
        slug = re.sub(r'[^a-z0-9]', '', ' '.join(title.split()[:2]).lower())
    base = '%s%s' % (slug[:24] or 'ref', year or '')
    key, n = base, 1
    while key in taken:
        n += 1
        key = '%s%s' % (base, chr(ord('a') + n - 2))
    return key


def render_entry(key, title, authors, year, venue_act, arxiv_id):
    """Emit one .bib entry in the project's canonical layout."""
    if venue_act and venue_act.get('book'):
        typ = 'inproceedings' if venue_act['kind'] == 'conf' else 'article'
        vfield = 'booktitle' if venue_act['kind'] == 'conf' else 'journal'
        vvalue, note = venue_act['book'], venue_act.get('note', '')
    else:
        typ, vfield = 'article', 'journal'
        vvalue = 'arXiv preprint arXiv:%s' % arxiv_id if arxiv_id else ''
        note = ''
    rows = [('title', protect_caps(title)),
            ('author', ('{%s}' % ' '.join(str(authors[0]).split()))
             if authors and CORP_AUTHOR.search(' '.join(str(authors[0]).split()))
             else ' and '.join(bib_author(a) for a in (authors or []))),
            (vfield, vvalue), ('year', str(year or '')), ('note', note)]
    rows = [(k, v) for k, v in rows if v]
    w = max(len(k) for k, _ in rows)
    body = ',\n'.join('  %-*s = {%s}' % (w, k, v) for k, v in rows)
    return '@%s{%s,\n%s\n}\n' % (typ, key, body)


def cmd_add(bib_path, query, am_key, use_dblp, dry_run):
    """Look a paper up across the sources and append a verified .bib entry.

    Refuses rather than guesses. Nothing is written unless at least one
    independent source confirmed the paper exists as described -- inventing a
    plausible-looking entry is the exact failure this tool exists to prevent.
    """
    q = query.strip()
    aid = re.fullmatch(r'(?:arxiv:)?(\d{4}\.\d{4,5})(v\d+)?', q, re.I)
    doi = re.fullmatch(r'(?:doi:)?(10\.\d{4,9}/\S+)', q, re.I)
    stub = {'arxiv': aid.group(1) if aid else None,
            'title': '' if (aid or doi) else q}

    ax = q_arxiv(stub) if not doi else {'title': None, 'authors': None,
                                        'year': None, 'id': None, 'err': 'skipped'}
    if aid and not ax.get('title'):
        # Export API rate-limited: the abs page is limited separately.
        ab = q_arxiv_abs(aid.group(1))
        if ab.get('title'):
            ax = ab
    dv = q_doi(doi.group(1), '') if doi else None
    title = ax.get('title') or (dv or {}).get('title')
    # AMiner writes the entry: its full author list and year come first, and
    # arXiv / doi.org fill in only what it lacks.
    rec = q_aminer_record(title or stub['title'], am_key) if am_key else None
    arec = rec if rec and not rec.get('err') else {}
    if not title and arec:
        title = fix_caret(arec['title'])
    if not title:
        print("✗ 查不到这篇:%s" % q)
        print("  arXiv / DOI 都没有命中。换个更准确的标题,或直接给 arXiv id / DOI。")
        print("  没有任何来源能证实的条目,不会写进 .bib —— 这正是这个工具存在的理由。")
        return 2

    authors = arec.get('authors') or ax.get('authors') or (dv or {}).get('authors')
    arxiv_id = ax.get('id') or arec.get('arxiv')

    orv = q_openreview(title)
    cr = q_crossref(title)
    am = q_aminer(title, am_key) if am_key else None
    dbl = q_dblp(title) if use_dblp else None
    st, suggest, ev = classify(orv, cr, dbl, am)

    anchors = []
    if ax.get('title'):
        anchors.append('arXiv:' + (arxiv_id or 'title-match'))
    if dv and dv.get('ok'):
        anchors.append('doi:' + doi.group(1))
    if any(x.startswith('OR:') for x in ev):
        anchors.append('openreview')
    if any(x.startswith(('CR:', 'DBLP:')) for x in ev):
        anchors.append('crossref/dblp')
    if any(x.startswith('AMINER:') for x in ev) or arec:
        anchors.append('aminer')
    if not anchors:
        print("✗ 找到了标题,但没有任何独立来源能证实它:%s" % title)
        print("  不写入。请人工核对原文后手写这一条。")
        return 2

    bib_year = arec.get('year') or ax.get('year') or (dv or {}).get('year')
    venue_act = pick_venue(suggest, bib_year, arxiv_id) if suggest else None
    year = (venue_act or {}).get('year') or bib_year or ''
    if not authors or not str(year).strip():
        print("✗ 没有来源给出作者或年份,不写入:%s" % title)
        print("  没有作者或年份的条目等于没核实。确认 AMiner key 可用,或换 arXiv id / 标题重试。")
        return 2

    existing = parse_bib(bib_path)
    dup = next((e for e in existing if sim(e['title'], title) >= 0.90), None)
    if dup:
        print("· 这篇已经在 .bib 里了:%s" % dup['key'])
        print("  当前出处:%s" % dup['current'])
        print("  要更新出处就跑:--only %s --fix" % dup['key'])
        return 1

    key = make_key(title, year, {e['key'] for e in existing}, authors)
    entry = render_entry(key, title, authors, year, venue_act, arxiv_id)

    print("标题  : %s" % title)
    print("作者  : %d 位,来自 %s" % (len(authors), 'AMiner' if arec.get('authors') else
                                    ('arXiv' if ax.get('authors') else 'doi.org')))
    print("出处  : %s" % ((venue_act or {}).get('book') or
                          ('arXiv preprint arXiv:%s' % arxiv_id if arxiv_id else '(无)')))
    print("锚点  : %s" % ', '.join(anchors))
    if ev:
        print("证据  : %s" % ' || '.join(ev[:3]))
    print("\n%s" % entry)
    if dry_run:
        print("(--dry-run:未写入)")
        return 0

    src = open(bib_path, encoding='utf-8').read()
    shutil.copyfile(bib_path, bib_path + '.bak')
    with open(bib_path, 'w', encoding='utf-8') as f:
        f.write(src.rstrip('\n') + '\n\n' + entry)
    print("✅ 已追加到 %s(备份 %s.bak),citation key: %s" % (bib_path, bib_path, key))
    print("   正文里用:\\citep{%s}" % key)
    return 0


def anchor_flag(anchors, errs):
    """The note for an entry no independent source anchored, or '' if one did.

    「查过、没命中」和「根本没查成」在这里长得一模一样:限流(429)或超时会让
    arXiv/OpenReview/Crossref 全部空手而归,锚点同样是空的。混为一谈是危险的
    —— 它把一条正确的条目报成「查无此文」,而下一步动作是去改它。实测:一轮
    全量重查里 63 条有 4 条这样标红,四条的 errs 全是 429、arxiv_title 全是
    None,查询压根没发出去。两种都算 need_action(没验过就是没过),但话得说对。
    """
    if anchors:
        return ''
    if errs:
        return ' | 🟡本轮未验证(源被限流/超时,不等于查无此文;单独重跑本条)'
    return ' | 🔴无独立验证锚点(arXiv/DOI/OpenReview 都没命中,须人工核原文)'


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('bib')
    ap.add_argument('--only', help='逗号分隔的 citation key,只查这些')
    ap.add_argument('--refresh', action='store_true', help='忽略缓存重查')
    ap.add_argument('--json', help='把结果同时写成 JSON')
    ap.add_argument('--pause', type=float, default=0.0,
                    help='在每个源的最小间隔之上再加的秒数(默认 0;限流严重时调大)')
    ap.add_argument('--fix', action='store_true',
                    help='把查到的正式出处写回 .bib,并统一成 Proceedings of ... 格式(先存 .bak)')
    ap.add_argument('--no-dblp', action='store_true', help='跳过 DBLP 探测')
    ap.add_argument('--no-aminer', action='store_true', help='跳过 AMiner(即使有 key)')
    ap.add_argument('--uncited', metavar='TEX',
                    help='列出 .bib 里没被这个 .tex 引用的条目(支持跨行 \\citep)')
    ap.add_argument('--add', metavar='TITLE|ARXIV_ID|DOI',
                    help='查证后生成一条格式正确的 bib 条目并追加(查不到就拒绝写入)')
    ap.add_argument('--dry-run', action='store_true',
                    help='配合 --add:只打印生成的条目,不写文件')
    a = ap.parse_args()
    globals()['EXTRA_GAP'] = a.pause

    if a.uncited:
        # 必须跨行匹配:\citep{a,b,%\n c} 用行式 grep 会漏,会把已引用的条目误报为未引用
        tex = open(a.uncited, encoding='utf-8').read()
        cited = set()
        for m in re.finditer(r'\\[a-zA-Z]*cite[a-zA-Z]*\s*(?:\[[^\]]*\])*\s*\{([^}]*)\}',
                             tex, re.S):
            for k in m.group(1).replace('%', ' ').split(','):
                if k.strip():
                    cited.add(k.strip())
        keys = [e['key'] for e in parse_bib(a.bib)]
        dead = [k for k in keys if k not in cited]
        for k in dead:
            print("UNCITED: %s" % k)
        print("\n==== %d 条中 %d 条未被引用 ====" % (len(keys), len(dead)))
        return 1 if dead else 0

    AM_KEY = '' if a.no_aminer else aminer_key()
    if AM_KEY:
        print("· AMiner 已启用(第五源)\n")
    use_dblp = (not a.no_dblp) and dblp_reachable()
    if not a.no_dblp and not use_dblp:
        print("· DBLP 不可达(云主机出口常被其拒绝),本轮用 arXiv+OpenReview+Crossref 三源\n")

    if a.add:
        return cmd_add(a.bib, a.add, AM_KEY, use_dblp, a.dry_run)

    entries = parse_bib(a.bib)
    if a.only:
        want = {k.strip() for k in a.only.split(',')}
        entries = [e for e in entries if e['key'] in want]

    cache_path = os.path.join(os.path.dirname(os.path.abspath(a.bib)), '.refcache.json')
    cache = {}
    # Always LOAD the cache, even under --refresh. --refresh means "do not
    # trust the rows for the entries I am checking", not "throw away the rows
    # for the entries I am not". Starting from {} and then dumping the dict
    # deleted every row this run did not touch: one
    # `--only <key> --refresh` took a 63-row cache down to 4, so the next full
    # sweep had to re-query everything, walked straight into the rate limit,
    # and reported entries as unverified that had been verified minutes before.
    # A refresh that destroys evidence makes the next run worse, not fresher.
    if os.path.exists(cache_path):
        try:
            cache = json.load(open(cache_path, encoding='utf-8'))
        except Exception:
            cache = {}

    results, need_action, plan = [], 0, {}
    for i, e in enumerate(entries, 1):
        ck = e['key'] + '|' + norm(e['title'])[:80]
        cached = None if a.refresh else cache.get(ck)
        # Two reasons never to trust a cached row blindly:
        #  - it carries an API error: that is a failure that happened to be
        #    written down, not a finding. Treating a 429 as "checked, nothing
        #    found" is exactly how an unverified entry passes as clean.
        #  - it predates the current schema: it has no anchor list, so it would
        #    be indistinguishable from an entry nothing could confirm.
        #  - its suggestions still carry a venue OpenReview marks withdrawn or
        #    rejected: it was classified before classify() refused those.
        c_bad = or_refused(or_evidence((cached or {}).get('evidence')))
        if (cached and not cached.get('errs') and cached.get('v') == CACHE_V
                and not any(s != 'openreview' and refused(v.split('|')[0], None, c_bad)
                            for s, v in cached.get('suggest') or [])):
            r = cached
        else:
            # AMiner first: it is the primary venue source, and asking it up
            # front means a run that dies mid-sweep still recorded the answer
            # the other four structurally cannot give.
            am = q_aminer(e['title'], AM_KEY) if AM_KEY else None
            ax = q_arxiv(e)
            orv = q_openreview(e['title'])
            cr = q_crossref(e['title'])
            dbl = q_dblp(e['title']) if use_dblp else None
            st, main_v, ev = classify(orv, cr, dbl, am)
            dv = q_doi(e['doi'], e['title']) if e['doi'] else None
            # What INDEPENDENTLY confirms this entry exists as described?
            anchors = []
            if ax['title']:
                anchors.append('arXiv:' + (e['arxiv'] or 'title-match'))
            if dv and dv['ok']:
                anchors.append('doi:' + e['doi'])
            if any(x.startswith('OR:') for x in ev):
                anchors.append('openreview')
            if any(x.startswith(('CR:', 'DBLP:')) for x in ev):
                anchors.append('crossref/dblp')
            if any(x.startswith('AMINER:') for x in ev):
                anchors.append('aminer')
            r = dict(v=CACHE_V, status=st, suggest=main_v, evidence=ev,
                     arxiv_title=ax['title'], arxiv_authors=ax['authors'],
                     arxiv_jref=ax['jref'], anchors=anchors,
                     doi_title=(dv or {}).get('title'),
                     doi_venue=(dv or {}).get('venue'),
                     errs=[x for x in (ax['err'], orv['err'], cr['err'],
                                       (dv or {}).get('err'),
                                       (am or {}).get('err')) if x
                           and x not in ('no-doi', 'no-key', 'not-on-arxiv')])
            cache[ck] = r
            json.dump(cache, open(cache_path, 'w', encoding='utf-8'),
                      ensure_ascii=False, indent=1)

        # 判断当前 bib 写法是否已经正确
        cur = e['current']
        cur_is_arxiv = 'arxiv' in cur.lower()
        # bib 写的 venue 正是 OpenReview 记为撤稿/拒稿的那一届(StreamingT2V 曾被
        # 写成 ICLR 2025):它不是"已经写对的出处",铁律二不保护它。
        cur_refused = not cur_is_arxiv and refused(
            cur, e['year'], or_refused(or_evidence(r['evidence'])))
        flag = ''
        if r['status'] == 'PUBLISHED' and cur_is_arxiv:
            flag = '❗需改为正式出处'; need_action += 1
        elif r['status'] == 'PUBLISHED' and cur_refused:
            flag = '❗bib 写的出处在 OpenReview 上是撤稿/拒稿,需改为正式出处'; need_action += 1
        elif r['status'] == 'WORKSHOP_OR_REJECTED':
            flag = '⛔仅 workshop/被拒 —— 按收录标准应删除'; need_action += 1
        elif r['status'] == 'PREPRINT' and not cur_is_arxiv:
            flag = '⚠️ bib 写了正式出处但查不到,请人工确认'; need_action += 1
        # 标题勘误
        if r['arxiv_title'] and sim(e['title'], r['arxiv_title']) < 0.97:
            flag += ' | 📝标题与 arXiv 官方不一致'; need_action += 1
        anchor_note = anchor_flag(r.get('anchors'), r.get('errs'))
        if anchor_note:
            flag += anchor_note
            need_action += 1

        line = "[%02d] %-22s %-22s %s\n     bib now : %s\n     title   : %s\n" % (
            i, e['key'], r['status'], flag, cur[:60], e['title'][:76])
        if r['suggest']:
            line += "     建议    : %s\n" % '; '.join(v for _, v in r['suggest'])
        line += "     锚点    : %s\n" % (', '.join(r.get('anchors') or []) or '(无)')
        if r.get('doi_venue'):
            line += "     DOI出处 : %s\n" % r['doi_venue'][:70]
        if r['evidence']:
            line += "     证据    : %s\n" % ' || '.join(r['evidence'][:4])
        if r['errs']:
            line += "     API错误 : %s\n" % r['errs']
        if r['arxiv_title'] and sim(e['title'], r['arxiv_title']) < 0.97:
            line += "     arXiv官方标题: %s\n" % r['arxiv_title'][:76]
        # ---- 统一格式:会议一律 Proceedings of <全称>,期刊用官方刊名 ----
        act = {}
        if r['arxiv_title'] and sim(e['title'], r['arxiv_title']) < 0.97:
            act['title'] = r['arxiv_title']
        # A venue already in the bib is authoritative: many papers appear both at
        # a conference and later in a journal (VBench is CVPR 2024 *and* shows a
        # TPAMI record), so promoting from the suggestion list would silently
        # re-cite it to the wrong one. Only reformat what is already there;
        # consult the suggestions solely to promote an arXiv preprint -- or to
        # replace a venue OpenReview itself records as withdrawn/rejected.
        cur_abbr, cur_spec = ((None, None) if cur_is_arxiv or cur == '?' or cur_refused
                              else canon_venue(cur))
        if cur_abbr:
            if norm(cur) != norm(cur_spec['book']):
                act.update(kind=cur_spec['kind'], book=cur_spec['book'])
        elif r['suggest']:
            chosen = pick_venue(r['suggest'], e['year'], e['arxiv'])
            if chosen:
                act.update(chosen)
        if act:
            plan[e['key']] = act
            if act.get('book') and not flag:
                flag = '🔧格式待统一'
                need_action += 1

        print(line, end='', flush=True)
        results.append(dict(key=e['key'], **r, bib_current=cur, flag=flag))

    print("\n==== 汇总: %d 条,%d 条需处理 ====" % (len(entries), need_action))
    if plan and not a.fix:
        print("   (加 --fix 可自动写回:%s)" % ', '.join(sorted(plan)[:6])
              + (' …' if len(plan) > 6 else ''))
    if a.fix and plan:
        done = apply_fixes(a.bib, plan)
        print("✅ 已改写 %d 条,原文件备份在 %s.bak" % (len(done), a.bib))
        print("   改动: %s" % ', '.join(done))
        print("   下一步: bibtex 重编译,并确认正文引用仍然通顺")
        need_action = 0
    if a.json:
        json.dump(results, open(a.json, 'w', encoding='utf-8'), ensure_ascii=False, indent=1)
    return 1 if need_action else 0


if __name__ == '__main__':
    sys.exit(main())
