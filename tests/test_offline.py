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


# --------------------------------------------------------------------- report
print("\n%s" % ("=" * 52))
if FAIL:
    print("%d test(s) FAILED: %s" % (len(FAIL), ', '.join(FAIL)))
    sys.exit(1)
print("all offline tests passed")
