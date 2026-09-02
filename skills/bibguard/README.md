# bibguard

Verify that every citation exists, recover where it was really published, add
new entries only after checking them, and put the whole bibliography in one
format. One Python file, standard library only, Python 3.8+. No `pip install`,
and no API key is required.

```bash
python3 scripts/bibguard.py references.bib
```

## Commands

```bash
S=scripts/bibguard.py

python3 $S references.bib --add "Attention Is All You Need"  # verify, then append
python3 $S references.bib --add 2506.08009    # an arXiv id or a DOI works too
python3 $S references.bib                     # report (cached, safe to re-run)
python3 $S references.bib --fix               # write venues + one format back
python3 $S references.bib --only k1,k2        # just these keys
python3 $S references.bib --refresh           # ignore the cache, re-query
python3 $S references.bib --json out.json     # machine-readable
python3 $S references.bib --uncited main.tex  # entries the paper never cites
python3 $S references.bib --pause 2           # go slower if you are rate-limited
python3 $S references.bib --no-aminer         # skip a source
python3 $S references.bib --no-dblp
```

`--dry-run` prints without writing. A `.bak` is saved before any write.

**Exit code 0 = nothing to do, 1 = something needs attention**, so it works as a
submission gate:

```yaml
- run: python3 skills/bibguard/scripts/bibguard.py references.bib --refresh
```

Results are cached in `.refcache.json` next to the `.bib`, so an interrupted run
resumes without re-querying. Add it to `.gitignore` along with `*.bak`.

## Adding a citation

Give it a title, an arXiv id or a DOI. It verifies the paper first, then writes
the entry:

```
$ python3 scripts/bibguard.py references.bib --add "LongLive: Real-time Interactive Long Video Generation"

@inproceedings{longlive2026,
  title     = {{LongLive}: Real-time Interactive Long Video Generation},
  author    = {Yang, Shuai and Huang, Wei and ... and Chen, Yukang},
  booktitle = {Proceedings of the International Conference on Learning Representations (ICLR)},
  year      = {2026},
  note      = {Poster; arXiv:2509.22622}
}
```

It handles the details that are easy to get wrong by hand:

- **Author names inverted** to BibTeX's `Last, First`, with lowercase particles
  kept on the surname (`van den Berg, Rianne`).
- **Acronyms braced** — `{MuKV}`, `{KV}`, `{NVFP4}` — or a lowercasing `.bst`
  renders "MuKV" as "Mukv". Hyphenated title case is left alone.
- **A citation key in your bibliography's own shape**: the short name before the
  colon plus the year, `longlive2026`. Collisions get a suffix.
- **Title, authors and year taken from the authoritative record**, not from what
  you typed. The name you know a paper by is often its old one.

And three cases where it refuses to write, which is what the name means:

| Situation | What happens |
|---|---|
| The paper cannot be found | Refused. **It will not invent a plausible entry.** |
| Found, but no independent anchor | Refused. Check the paper yourself and write it by hand. |
| Already in your `.bib` | Reports the existing key and how to update its venue instead. |

## What it reports

```
[07] selfforcing2025        PUBLISHED
     bib now : arXiv preprint arXiv:2506.08009
     title   : Self Forcing: Bridging the Train-Test Gap in Autoregressive Video Diffusion
     建议    : NeurIPS 2025 spotlight; NeurIPS 2025|2025|doi:10.52202/085713-5576
     锚点    : arXiv:2506.08009, openreview, crossref, aminer
```

| Status | Meaning | What to do |
|---|---|---|
| `PUBLISHED` | A real conference or journal record was found | If the bib still says arXiv, run `--fix` |
| `PREPRINT` | Exists, no venue found | Keep `@article` and arXiv. Normal. |
| `WORKSHOP_OR_REJECTED` | Only workshop, rejected or under-review records | Decide whether your venue standard allows it |
| no anchor 🔴 | **Nothing could confirm this entry at all** | Open the paper yourself |

### Verified is not the same as unverifiable

The easiest way to fool yourself is to treat *"I asked and got nothing"* and
*"my request failed"* as one result. An HTTP 429 cached as a clean `PREPRINT`
looks exactly like a genuinely checked preprint in the report.

So every entry lists its **independent anchors** — `arXiv:xxxx.xxxxx`,
`doi:10.xxxx/...`, `openreview`, `crossref`, `aminer`. Zero anchors means
nothing verified it, and the report flags it 🔴. Rows carrying an API error are
never cached as findings; they are re-queried on the next run.

## Sources

| Source | Covers | Why it is there |
|---|---|---|
| **AMiner** | Almost every venue, including CMT-run conferences | The primary venue source. CVPR and ICCV are not on OpenReview and have no DOI until the proceedings ship, so for months this is the only source that knows a paper was accepted. Needs a free key. |
| **arXiv** | Title, authors, dates | The authoritative title, which is how renamed papers are caught. |
| **OpenReview** | ICLR, ICML, NeurIPS, COLM | Those venues issue no DOI, so Crossref and OpenAlex cannot see them. Also gives the decision grade. |
| **Crossref** | Anything with a DOI | Returns the DOI itself. |
| **doi.org** | Anything registered anywhere | Publisher-independent content negotiation, and the only machine anchor for a paper that was never on arXiv and never went through OpenReview. |
| **DBLP** | Cross-check | Used when reachable; probed once per run and skipped otherwise, so it never costs a timeout per entry. |

arXiv, OpenReview, Crossref and doi.org need no key and no registration. AMiner
needs a free key; without one it is skipped and the other four still work. Every
source is gated on a title similarity above 0.80, so a near miss is never
silently attributed.

**AMiner decides which venue, but never the details.** The DOI is still
harvested from Crossref and the acceptance grade (`Oral`, `spotlight`) from
OpenReview whenever they agree on the same venue. Preferring one source must not
cost you what only another source has.

```bash
export AMINER_API_KEY='...'          # or
echo '...' > ~/.claude/aminer_key    # chmod 600 — read automatically
```

> **Never put the key in your repo.** A `.bib` lives in git, and a key committed
> once stays in the history forever.

## Format rules `--fix` enforces

| Kind | Entry type | Field | Written as |
|---|---|---|---|
| Conference | `@inproceedings` | `booktitle` | `Proceedings of the <official name> (<ABBR>)` |
| Journal | `@article` | `journal` | The official journal name in full |
| Preprint | `@article` | `journal` | `arXiv preprint arXiv:XXXX.XXXXX` |

`booktitle` must **not** start with "In" — the `.bst` adds it, and the result is
"In In Proceedings of...".

Add a venue by editing [`scripts/venues.json`](scripts/venues.json):

```json
"SIGIR": {
  "kind": "conf",
  "book": "Proceedings of the International ACM SIGIR Conference on Research and Development in Information Retrieval (SIGIR)",
  "match": ["sigir", "research and development in information retrieval"]
}
```

`match` entries are lowercase substrings and the longest match wins, so `naacl`
beats a bare `acl`.

## Two things it will not do

**It will not re-point a venue you already got right.** Many papers have both a
conference and a journal record. The suggestion list is only consulted when the
bib currently says arXiv; when a recognizable venue is already there, the
wording is normalized and nothing else changes.

**It will not overwrite your `note`.** `spotlight`, `oral` and your own
annotations are merged rather than replaced, because no API can give them back.

## After `--fix`, verify

```bash
pdflatex main.tex && bibtex main && pdflatex main.tex && pdflatex main.tex
grep -cE '^!' main.log                     # LaTeX errors — must be 0
grep -c 'Citation.*undefined' main.log     # undefined citations — must be 0
python3 scripts/bibguard.py references.bib --uncited main.tex
```

Use `--uncited` rather than grep for unused entries. A `\citep{a,b,%` continued
across lines is a multi-line construct that a line-based grep misses, so it
reports entries that *are* cited as unused; deleting those breaks the paper.

## Tests

```bash
python3 tests/test_offline.py    # no network required
```
