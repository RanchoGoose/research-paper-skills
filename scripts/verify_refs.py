#!/usr/bin/env python3
"""
verify_refs.py — 交叉核对 .bib 里每条引用的真实发表出处。

三源分工(缺一不可):
  arXiv API       -> title / authors / 日期
  OpenReview API2 -> ICLR / ICML / NeurIPS / COLM 录用状态(这些会议不发 DOI,
                     Crossref 与 OpenAlex 都查不到)
  Crossref API    -> CVPR / ICCV / ECCV / ACL / SIGGRAPH / HPCA / 期刊(有 DOI 的)

用法:
  python3 verify_refs.py references.bib                 # 全量核对 + 报告
  python3 verify_refs.py references.bib --only k1,k2    # 只查指定 key
  python3 verify_refs.py references.bib --refresh       # 忽略缓存重查
  python3 verify_refs.py references.bib --json r.json   # 附带机器可读输出

退出码: 0 = 全部无需改动;1 = 有条目需要处理(可当投稿前 gate)。
缓存写在 <bib同目录>/.refcache.json,可安全重跑(API 有限流)。
"""
import argparse, difflib, json, os, re, shutil, socket, sys, time
import urllib.error, urllib.parse, urllib.request

UA = os.environ.get("REFVERIFY_UA", "ref-verify/2.0 (+bibliography verification)")
MAILTO = os.environ.get("REFVERIFY_MAILTO", "")

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
    r'IJCAI|SIGGRAPH|HPCA|ISCA|MICRO|ASPLOS|OSDI|SOSP|NSDI|MLSys|COLM|WACV|BMVC|'
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
        entries.append(dict(
            key=key, type=typ, doi=dm.group(1) if dm else None,
            title=re.sub(r'[{}\\]', '', f['title']),
            year=f.get('year', '?'),
            current=f.get('booktitle') or f.get('journal') or '?',
            arxiv=(re.search(r'(\d{4}\.\d{4,5})', f.get('journal', '') + ' ' + f.get('note', ''))
                   or [None, None])[1] if re.search(
                       r'(\d{4}\.\d{4,5})', f.get('journal', '') + ' ' + f.get('note', '')) else None,
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
                        'title': None, 'authors': None, 'jref': None}
            backoff(e, i, 6)
    for e in root.findall('a:entry', NS):
        ti = ' '.join((e.find('a:title', NS).text or '').split())
        if sim(entry['title'], ti) < 0.80:
            continue
        jr = e.find('a:journal_ref', NS)
        return {'err': None, 'title': ti,
                'authors': [a.find('a:name', NS).text for a in e.findall('a:author', NS)],
                'jref': jr.text if jr is not None else None}
    # "Not on arXiv" is an answer, not a failure -- plenty of real papers never
    # get posted (journal-only, Nature, older proceedings). Caching that as an
    # error would re-query it forever. But when the bib *gave* an id and the
    # title still does not match, that is a genuine discrepancy worth surfacing.
    return {'err': 'no-title-match' if entry['arxiv'] else 'not-on-arxiv',
            'title': None, 'authors': None, 'jref': None}


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
                'ok': False, 'title': None, 'venue': None}
    ti = d.get('title')
    ti = ti[0] if isinstance(ti, list) and ti else ti
    ven = d.get('container-title')
    ven = ven[0] if isinstance(ven, list) and ven else ven
    return {'err': None, 'ok': bool(ti) and sim(title, ti) >= 0.80,
            'title': ti, 'venue': ven}


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

    entries = parse_bib(a.bib)
    if a.only:
        want = {k.strip() for k in a.only.split(',')}
        entries = [e for e in entries if e['key'] in want]

    cache_path = os.path.join(os.path.dirname(os.path.abspath(a.bib)), '.refcache.json')
    cache = {}
    if os.path.exists(cache_path) and not a.refresh:
        try:
            cache = json.load(open(cache_path, encoding='utf-8'))
        except Exception:
            cache = {}

    results, need_action, plan = [], 0, {}
    for i, e in enumerate(entries, 1):
        ck = e['key'] + '|' + norm(e['title'])[:80]
        cached = cache.get(ck)
        # Two reasons never to trust a cached row blindly:
        #  - it carries an API error: that is a failure that happened to be
        #    written down, not a finding. Treating a 429 as "checked, nothing
        #    found" is exactly how an unverified entry passes as clean.
        #  - it predates the current schema: it has no anchor list, so it would
        #    be indistinguishable from an entry nothing could confirm.
        if cached and not cached.get('errs') and cached.get('v') == CACHE_V:
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
        flag = ''
        if r['status'] == 'PUBLISHED' and cur_is_arxiv:
            flag = '❗需改为正式出处'; need_action += 1
        elif r['status'] == 'WORKSHOP_OR_REJECTED':
            flag = '⛔仅 workshop/被拒 —— 按收录标准应删除'; need_action += 1
        elif r['status'] == 'PREPRINT' and not cur_is_arxiv:
            flag = '⚠️ bib 写了正式出处但查不到,请人工确认'; need_action += 1
        # 标题勘误
        if r['arxiv_title'] and sim(e['title'], r['arxiv_title']) < 0.97:
            flag += ' | 📝标题与 arXiv 官方不一致'; need_action += 1
        # 没有任何独立锚点 = 这条谁也没验过,必须人工看原文
        if not r.get('anchors'):
            flag += ' | 🔴无独立验证锚点(arXiv/DOI/OpenReview 都没命中,须人工核原文)'
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
        # consult the suggestions solely to promote an arXiv preprint.
        cur_abbr, cur_spec = (None, None) if cur_is_arxiv or cur == '?' else canon_venue(cur)
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
