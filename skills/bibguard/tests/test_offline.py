#!/usr/bin/env python3
"""Offline tests — no network, no API key, no dependencies.

Every case here is a bug that actually shipped once. Run before touching
bibguard.py:

    python3 tests/test_offline.py
"""
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(os.path.dirname(HERE), 'scripts'))
import bibguard as V                                       # noqa: E402

FAIL = []


def check(name, got, want):
    if got == want:
        print("  ok   %s" % name)
    else:
        print("  FAIL %s\n       got  %r\n       want %r" % (name, got, want))
        FAIL.append(name)


def section(t):
    print("\n%s" % t)


# --------------------------------------------------------------- venue naming
section("canon_venue — map any spelling onto one canonical booktitle")
check("bare abbreviation", V.canon_venue('CVPR 2025')[0], 'CVPR')
check("full name", V.canon_venue(
    '2025 IEEE/CVF Conference on Computer Vision and Pattern Recognition (CVPR)')[0], 'CVPR')
check("openreview style", V.canon_venue('ICLR 2026 Oral')[0], 'ICLR')
check("crossref long form", V.canon_venue(
    'Advances in Neural Information Processing Systems 38')[0], 'NEURIPS')
# longest match wins, or a bare "acl" substring would swallow naacl/emnlp
check("longest match wins", V.canon_venue('NAACL 2025')[0], 'NAACL')
check("unknown venue", V.canon_venue('Journal of Nothing In Particular')[0], None)

section("booktitle must not begin with 'In' — the .bst adds it")
bad = [k for k, s in V.VENUES.items() if s['book'].lower().startswith('in ')]
check("no leading 'In' in venues.json", bad, [])

# Idempotence: a bib already written in canonical form must be recognized as
# already-correct, or --fix would keep "changing" it on every run.
section("canon_venue is idempotent on its own output")
drift = sorted(k for k, s in V.VENUES.items() if V.canon_venue(s['book'])[0] != k)
check("every booktitle maps back to its own key", drift, [])


# ------------------------------------------------------------ source priority
section("pick_venue — AMiner decides the venue, others fill in the details")
sel = V.pick_venue([('openreview', 'NeurIPS 2025 spotlight'),
                    ('aminer', 'NeurIPS 2025|2025|doi:None'),
                    ('cr', 'Advances in Neural Information Processing Systems 38'
                           '|2025|doi:10.52202/085713-5576')], '2025', '2506.08009')
check("venue chosen", sel['book'],
      'Proceedings of the Conference on Neural Information Processing Systems (NeurIPS)')
# Preferring AMiner must not cost us what only the other sources carry.
check("keeps OpenReview's grade", 'spotlight' in sel['note'], True)
check("keeps Crossref's DOI", 'doi:10.52202/085713-5576' in sel['note'], True)
check("keeps the arXiv id", 'arXiv:2506.08009' in sel['note'], True)

# CMT venues: no OpenReview record, no DOI until proceedings ship.
solo = V.pick_venue([('aminer', 'CVPR 2026|2026|doi:None')], '2026', '2605.22269')
check("AMiner-only venue", solo['book'],
      'Proceedings of the IEEE/CVF Conference on Computer Vision and Pattern Recognition (CVPR)')
check("no bogus 'doi:None'", 'None' in solo['note'], False)

# A paper cited as its 2024 conference version must not be re-pointed at a reprint.
yr = V.pick_venue([('cr', 'CVPR 2026|2026|doi:None'),
                   ('cr', 'CVPR 2024|2024|doi:None')], '2024', None)
check("year matching the bib wins", yr['year'], '2024')
check("nothing recognizable", V.pick_venue([('cr', 'Some Local Symposium')], '2024', None), None)


# ---------------------------------------------------------------- classifying
section("classify — a workshop record does not make it a workshop paper")
st, main, _ = V.classify({'venues': ['ES-FoMO 2023 Poster', 'NeurIPS 2023 poster']},
                         {'venues': []})
check("main venue outranks workshop", st, 'PUBLISHED')
st, _, _ = V.classify({'venues': ['ICLR 2025 Conference Withdrawn Submission']},
                      {'venues': [{'venue': 'CVPR 2025', 'year': 2025, 'doi': 'x',
                                   'type': 'proceedings-article'}]})
check("withdrawn then republished", st, 'PUBLISHED')
st, _, _ = V.classify({'venues': ['ICML 2025 Workshop on Foo']}, {'venues': []})
check("workshop only", st, 'WORKSHOP_OR_REJECTED')
st, _, _ = V.classify({'venues': ['CoRR']}, {'venues': []})
check("CoRR is neither published nor rejected", st, 'PREPRINT')
st, _, _ = V.classify({'venues': []}, {'venues': []})
check("nothing found", st, 'PREPRINT')

section("classify — AMiner sorts first among the suggestions")
_, main, _ = V.classify(
    {'venues': ['ICLR 2026 Oral']},
    {'venues': [{'venue': 'ICLR 2026', 'year': 2026, 'doi': None,
                 'type': 'proceedings-article'}]},
    None,
    {'venues': [{'venue': 'ICLR 2026', 'year': 2026, 'doi': None,
                 'type': 'proceedings-article'}]})
check("aminer first", main[0][0], 'aminer')

# StreamingT2V: OpenReview says "ICLR 2025 ... Withdrawn", AMiner says a bare
# "ICLR 2025" (carrying the CVPR DOI). AMiner sorted first, so --add wrote ICLR.
section("classify — a venue OpenReview marks withdrawn is not taken from AMiner")
t2v_or = {'venues': ['CVPR 2025', 'ICLR 2025 Conference Withdrawn Submission']}
t2v_am = {'venues': [{'venue': 'ICLR 2025', 'year': None,
                      'doi': '10.1109/cvpr52734.2025.00245', 'type': 'proceedings-article'}]}
t2v_cr = {'venues': [{'venue': '2025 IEEE/CVF Conference on Computer Vision and Pattern '
                               'Recognition (CVPR)', 'year': 2025,
                      'doi': '10.1109/cvpr52734.2025.00245', 'type': 'proceedings-article'}]}
st, main, _ = V.classify(t2v_or, t2v_cr, None, t2v_am)
check("still published", st, 'PUBLISHED')
check("withdrawn ICLR dropped from the suggestions",
      any(V.canon_venue(v.split('|')[0])[0] == 'ICLR' for _, v in main), False)
check("CVPR proceedings chosen", V.pick_venue(main, '2025', None)['book'],
      'Proceedings of the IEEE/CVF Conference on Computer Vision and Pattern Recognition (CVPR)')
st, _, _ = V.classify({'venues': ['ICLR 2025 Conference Withdrawn Submission']},
                      {'venues': []}, None, t2v_am)
check("withdrawn + AMiner only -> not published", st, 'WORKSHOP_OR_REJECTED')
# Withdrawn one year, accepted the next: the accepted year must survive.
st, main, _ = V.classify({'venues': ['ICLR 2024 Conference Withdrawn Submission',
                                     'ICLR 2025 Poster']}, {'venues': []}, None,
                         {'venues': [{'venue': 'ICLR 2025', 'year': 2025, 'doi': None,
                                      'type': 'proceedings-article'}]})
check("other year accepted -> kept", (st, main[0][0]), ('PUBLISHED', 'aminer'))
bad = V.or_refused(['ICLR 2025 Conference Withdrawn Submission', 'CVPR 2025'])
check("bib naming the withdrawn venue is refused",
      V.refused('Proceedings of the International Conference on Learning Representations (ICLR)',
                '2025', bad), True)
check("bib naming the real venue is not",
      V.refused('Proceedings of the IEEE/CVF Conference on Computer Vision and Pattern '
                'Recognition (CVPR)', '2025', bad), False)
check("a workshop withdrawal says nothing about the main track",
      V.or_refused(['ICML 2025 Workshop on Foo Withdrawn Submission']), set())


# ------------------------------------------------------------------ bib edits
section("merge_note — never drop a hand-written annotation")
check("adds without clobbering", V.merge_note('spotlight', 'doi:10.1/x'),
      'spotlight; doi:10.1/x')
check("no duplicate DOI", V.merge_note('doi:10.1/x', 'doi:10.1/x'), 'doi:10.1/x')
check("same id, other prefix", V.merge_note('arXiv:2506.08009', 'arXiv:2506.08009'),
      'arXiv:2506.08009')
check("empty old", V.merge_note(None, 'doi:10.1/x'), 'doi:10.1/x')

section("split_fields — commas inside a field value are not separators")
check("braced comma", len(V.split_fields('title = {A, B}, year = {2025}')), 2)

section("parse_bib — reads the sample bibliography")
ents = V.parse_bib(os.path.join(HERE, 'sample.bib'))
check("entry count", len(ents), 4)
by = {e['key']: e for e in ents}
check("arXiv id extracted", by['selfforcing2025']['arxiv'], '2506.08009')
check("DOI extracted from note", by['causvid2024']['doi'], '10.1109/CVPR52734.2025.02138')
# "cvpr52734.2025.02138" once came back as arXiv id 2734.2025 and --fix wrote it
# into the note.
check("no arXiv id read out of a DOI", by['causvid2024']['arxiv'], None)
check("current venue read", by['vbench2024']['current'], 'CVPR 2024')

section("set_field — the last field of an entry must not be duplicated")
body = "\n  title = {A},\n  year = {2025}"
out = V.set_field(body, 'year', '2026')
check("year replaced once", out.count('year ='), 1)
check("new value written", '2026' in out and '2025' not in out, True)

section("tidy — no trailing comma, no blank lines left by a dropped field")
check("cleans up", V.tidy("\n  a = {1},\n\n\n  b = {2},\n"), "\n  a = {1},\n  b = {2}")


# -------------------------------------------------------------------- uncited
section("--uncited must match \\citep across line breaks")
import re                                                     # noqa: E402
tex = "text \\citep{alpha,beta,%\n  gamma} and \\citet[p.~3]{delta}."
cited = set()
for m in re.finditer(r'\\[a-zA-Z]*cite[a-zA-Z]*\s*(?:\[[^\]]*\])*\s*\{([^}]*)\}', tex, re.S):
    for k in m.group(1).replace('%', ' ').split(','):
        if k.strip():
            cited.add(k.strip())
# A line-based grep misses gamma and reports a cited entry as unused; deleting
# what it names removes a citation the paper is actually using.
check("all four found", sorted(cited), ['alpha', 'beta', 'delta', 'gamma'])


# ------------------------------------------------------------------ title sim
section("similarity gate — a near-miss must never be silently attributed")
check("same paper, punctuation differs",
      V.sim('Self Forcing: Bridging the Train-Test Gap',
            'Self-Forcing: Bridging the Train Test Gap') > 0.80, True)
check("different paper", V.sim('Attention Is All You Need',
                               'Diffusion Models Beat GANs') > 0.80, False)

section("--add: bib_author — arXiv gives 'First Last', BibTeX wants 'Last, First'")
check("plain name", V.bib_author('Xun Huang'), 'Huang, Xun')
check("middle name", V.bib_author('Song Han Lee'), 'Lee, Song Han')
check("lowercase particle", V.bib_author('Rianne van den Berg'),
      'van den Berg, Rianne')
check("already inverted", V.bib_author('Huang, Xun'), 'Huang, Xun')
check("mononym", V.bib_author('Plato'), 'Plato')

section("--add: protect_caps — an unbraced acronym renders as 'Mukv'")
check("acronym braced", V.protect_caps('MuKV: Multi-Grained KV Cache'),
      '{MuKV}: Multi-Grained {KV} Cache')
check("camel case braced", V.protect_caps('LongLive is real-time'),
      '{LongLive} is real-time')
check("ordinary words untouched", V.protect_caps('Attention is all you need'),
      'Attention is all you need')

section("--add: make_key — same shape as the rest of the bibliography")
check("head before colon + year",
      V.make_key('Self Forcing: Bridging the Train-Test Gap', '2025', set()),
      'selfforcing2025')
check("acronym title", V.make_key('MuKV: Multi-Grained KV', '2026', set()), 'mukv2026')
check("collision gets a suffix",
      V.make_key('MuKV: Multi-Grained KV', '2026', {'mukv2026'}), 'mukv2026a')
# Slicing a long title mid-word gives keys like "attentionisallyounee2017";
# fall back to the other standard convention instead.
check("no colon -> first author surname",
      V.make_key('Attention Is All You Need', '2017', set(), ['Ashish Vaswani']),
      'vaswani2017')
check("colon head too long -> surname",
      V.make_key('Towards a General Theory of Everything: A Study', '2024', set(),
                 ['Jane Roe']), 'roe2024')
check("no colon and no authors", 
      V.make_key('Attention Is All You Need', '2017', set(), None), 'attentionis2017')

section("--add: render_entry — canonical layout, nothing invented")
e = V.render_entry('longlive2026', 'LongLive: Real-time Interactive Long Video Generation',
                   ['Shuai Yang', 'Yukang Chen'], '2026',
                   {'kind': 'conf', 'book': 'Proceedings of the International Conference on '
                                            'Learning Representations (ICLR)',
                    'note': 'Poster; arXiv:2509.22622'}, '2509.22622')
check("conference -> @inproceedings", e.startswith('@inproceedings{longlive2026,'), True)
check("uses booktitle", '  booktitle = {Proceedings of the International Conference' in e, True)
check("authors inverted and joined", 'Yang, Shuai and Chen, Yukang' in e, True)
check("acronym protected", '{LongLive}' in e, True)
check("note carried", 'note      = {Poster; arXiv:2509.22622}' in e, True)
# No venue found: it must stay an honest preprint rather than guess one.
p = V.render_entry('foo2026', 'Foo Bar', ['A B'], '2026', None, '2601.00001')
check("no venue -> @article + arXiv", p.startswith('@article{foo2026,'), True)
check("journal is the arXiv line", 'journal = {arXiv preprint arXiv:2601.00001}' in p, True)
check("no empty fields emitted", '{}' in p, False)

section("--add: corporate author — 'Gemma Team' is one author, not 'Team, Gemma'")
g = V.render_entry('gemma2026', 'Gemma 4 Technical Report',
                   ['Gemma Team', 'Sherif El Abd', 'Vaibhav Aggarwal'], '2026', None, '2607.02770')
check("team braced as the author", 'author  = {{Gemma Team}}' in g, True)
check("team key uses the team name", V.make_key('Gemma 4 Technical Report', '2026', set(),
                                                ['Gemma Team', 'Sherif El Abd']), 'gemma2026')
check("a person is still inverted", 'Park, Joon Sung' in V.render_entry(
    'x2023', 'X', ['Joon Sung Park'], '2023', None, None), True)

section("--add: AMiner paper/info writes the entry (authors, year, arXiv id)")
rec = V.aminer_info_parse({'success': True, 'data': [{
    'id': '6528a864939a5f408257a128', 'title': 'MemGPT: Towards LLMs As Operating Systems',
    'authors': [{'name': 'Charles Packer'}, {'name': 'Sarah  Wooders'}, {}],
    'year': 2023, 'doi': '10.48550/arxiv.2310.08560'}]})
check("full author list, blanks dropped", rec['authors'], ['Charles Packer', 'Sarah Wooders'])
check("year as string", rec['year'], '2023')
check("arXiv id from the DataCite DOI", rec['arxiv'], '2310.08560')
rec2 = V.aminer_info_parse({'success': True, 'data': [{
    'id': 'x', 'title': 'Generative Agents', 'authors': [{'name': 'Joon Sung Park'}],
    'year': 2023, 'venue': {'raw': 'UIST'}, 'doi': '10.1145/3586183.3606763'}]})
check("venue raw unwrapped", rec2['venue'], 'UIST')
check("no arXiv id from a publisher DOI", rec2['arxiv'], None)
check("failed response -> None", V.aminer_info_parse({'success': False, 'data': []}), None)

section("--add: aminer_queries — AMiner misses titles with math, finds the words after the colon")
check("full, plain, tail", V.aminer_queries('A$^2$RD: Agentic Autoregressive Diffusion for Long Video'),
      ['A$^2$RD: Agentic Autoregressive Diffusion for Long Video',
       'A2RD: Agentic Autoregressive Diffusion for Long Video',
       'Agentic Autoregressive Diffusion for Long Video'])
check("plain title not repeated", V.aminer_queries('Gemma 4 Technical Report'),
      ['Gemma 4 Technical Report'])
check("too-short tail skipped", V.aminer_queries('MemGPT: Towards LLMs'), ['MemGPT: Towards LLMs'])

section("--add: arxiv.org/abs meta tags stand in for a rate-limited API")
page = ('<meta name="citation_title" content="A$^2$RD: Agentic Autoregressive Diffusion" />'
        '<meta name="citation_author" content="Long, Do Xuan" />'
        '<meta name="citation_author" content="Song, Yale" />'
        '<meta name="citation_date" content="2026/05/07" />')
ab = V.arxiv_abs_parse(page)
check("title kept with its math", ab['title'], 'A$^2$RD: Agentic Autoregressive Diffusion')
check("authors already inverted", ab['authors'], ['Long, Do Xuan', 'Song, Yale'])
check("year from citation_date", ab['year'], '2026')
check("no meta -> None", V.arxiv_abs_parse('<html></html>'), None)

section("--add: fix_caret — a bare ^ from AMiner would break LaTeX")
check("caret wrapped in math", V.fix_caret('A^2RD: Agentic'), 'A$^2$RD: Agentic')
check("existing math untouched", V.fix_caret('A$^2$RD: Agentic'), 'A$^2$RD: Agentic')
check("key from the fixed title", V.make_key(V.fix_caret('A^2RD: Agentic'), '2026', set()),
      'a2rd2026')

section("--add: doi.org CSL gives authors and year (a DOI add once wrote neither)")
au, yr = V.csl_authors_year({'author': [{'given': 'Joon Sung', 'family': 'Park'},
                                         {'literal': 'OpenAI'}, {'family': 'Plato'}],
                             'issued': {'date-parts': [[2023, 10, 29]]}})
check("family, given", au, ['Park, Joon Sung', 'OpenAI', 'Plato'])
check("year", yr, '2023')
check("empty record", V.csl_authors_year({}), ([], None))
check("UIST is a main venue", bool(V.MAIN_VENUE.match('UIST')), True)
check("UIST canonical", V.canon_venue(
    'Proceedings of the 36th Annual ACM Symposium on User Interface Software and Technology')[0],
    'UIST')

section("short_query — OpenReview ranks badly on very long terms")
# The 12-word cap is the fix: a full 20-word title returns records with
# venue=None and buries the real hit past the result limit.
check("caps at 12 words", len(V.short_query(' '.join('w%d' % i for i in range(30))).split()), 12)
# A descriptive head is distinctive enough to stand alone...
check("uses a descriptive head", V.short_query(
    'Consistent Autoregressive Video Generation: A Study of Long Contexts'),
    'Consistent Autoregressive Video Generation')
# ...but a one- or two-word product name is not, so keep the whole title.
check("keeps title when head is a bare name", V.short_query(
    'LongLive: Real-time Interactive Long Video Generation'),
    'LongLive: Real-time Interactive Long Video Generation')


# ------------------------------------------------------- anchors vs. rate limit
section("anchor_flag — a lookup that never ran is not a lookup that found nothing")
check("anchored entry is silent",
      V.anchor_flag(['arxiv:2606.17800'], []), "")
check("anchored wins even if some other source errored",
      V.anchor_flag(['openreview', 'aminer'], ['HTTPError:HTTP Error 429']), "")
check("no anchor, no error -> genuinely unfound, read the paper",
      '🔴' in V.anchor_flag([], []), True)
check("no anchor because 429 -> says unverified, not unfound",
      '🟡' in V.anchor_flag([], ['HTTPError:HTTP Error 429: Too Many Requests']), True)
check("a rate-limited entry is never called 查无此文",
      '🔴' in V.anchor_flag([], ['TimeoutError:The read operation timed out']), False)
check("None anchors behaves like empty",
      '🟡' in V.anchor_flag(None, ['HTTPError:HTTP Error 429']), True)

# ------------------------------------------------- duplicate arXiv id in note
section("dup_arxiv_note — a preprint must not print its arXiv id twice")
check("wan: note repeats the journal id -> drop the note",
      V.dup_arxiv_note('arXiv preprint arXiv:2503.20314', 'arXiv:2503.20314'), '')
check("other tokens survive",
      V.dup_arxiv_note('arXiv preprint arXiv:2503.20314',
                       'Oral; arXiv:2503.20314; doi:10.1/x'), 'Oral; doi:10.1/x')
check("different id is not a duplicate",
      V.dup_arxiv_note('arXiv preprint arXiv:2503.20314', 'arXiv:2401.01256'), None)
check("published venue is left alone",
      V.dup_arxiv_note('Proceedings of the IEEE/CVF Conference on Computer Vision and Pattern Recognition (CVPR)',
                       'arXiv:2503.20314'), None)
check("no note, nothing to do",
      V.dup_arxiv_note('arXiv preprint arXiv:2503.20314', ''), None)
import tempfile                                            # noqa: E402
with tempfile.TemporaryDirectory() as d:
    bp = os.path.join(d, 'x.bib')
    open(bp, 'w').write('@article{wan2025,\n  title   = {Wan},\n'
                        '  journal = {arXiv preprint arXiv:2503.20314},\n'
                        '  year    = {2025},\n  note    = {arXiv:2503.20314}\n}\n')
    V.apply_fixes(bp, {'wan2025': {'note_set': ''}})
    out = open(bp).read()
    check("apply_fixes drops the repeated note", 'note' in out, False)
    check("apply_fixes keeps the journal id", 'arXiv:2503.20314' in out, True)

# --------------------------------------------------------------------- report
print("\n%s" % ("=" * 52))
if FAIL:
    print("%d test(s) FAILED: %s" % (len(FAIL), ', '.join(FAIL)))
    sys.exit(1)
print("all offline tests passed")
