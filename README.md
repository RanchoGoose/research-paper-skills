# Research Paper Skills

Three independent Agent Skills for the parts of a paper that can actually be
checked: the bibliography, the manuscript, and the review.

| Skill | What it does |
|---|---|
| [**bibguard**](skills/bibguard/) | Verify that every citation exists, recover where it was really published, add new entries only after checking them, and put the whole `.bib` in one format. |
| [**iclr-paper-review**](skills/iclr-paper-review/) | Review a machine-learning paper against a strict ICLR-style rubric: novelty, claim-to-evidence, equations, every figure and table, experimental sufficiency, and one calibrated 1–10 score. |
| [**paper-writing**](skills/paper-writing/) | The writing rules as a per-section template — outline before prose, numbers in tables, every claim with its evidence — plus `paperlint`, which turns the measurable ones into a command with an exit code. |

Each skill is self-contained and can be installed on its own. None of them
invokes or depends on another.

[中文说明](README.zh-CN.md) · [MIT](LICENSE)

## Install

All three, globally, for Codex:

```bash
npx skills add RanchoGoose/research-paper-skills --skill '*' -g -a codex -y
```

One at a time, and to see what is available first:

```bash
npx skills add RanchoGoose/research-paper-skills --skill bibguard -g -a codex -y
npx skills add RanchoGoose/research-paper-skills --list
```

Replace `codex` with `claude-code` for Claude Code. To install from a clone, or
into a single project:

```bash
git clone https://github.com/RanchoGoose/research-paper-skills.git
cd research-paper-skills
bash install.sh all --claude --user
bash install.sh bibguard --claude /path/to/paper
```

Both CLIs are plain Python 3.8+ with the standard library only. No `pip install`
and no API key is required to run them.

## bibguard

**Your `.bib`, guarded.** A citation is verified before it is written, never
after. Three things go wrong in a bibliography, and `bibguard` covers all three:

- **The paper does not exist.** A model invented a plausible title, or you
  copied a citation from a paper that had already invented it.
- **The venue is wrong.** You cited the preprint; it has since appeared at
  NeurIPS. Or the paper was renamed and your title is the old one.
- **The format is inconsistent.** Half the entries say `CVPR 2025`, half give
  the full proceedings name, and one renders as "In In Proceedings of".

The part that matters most is that it reports **which entries it could not
verify**, instead of quietly passing them. Every entry carries its independent
anchors — arXiv ID, DOI, OpenReview, Crossref, AMiner — and an entry with none
is flagged for you to check by hand. `--add` refuses to write an entry it could
not confirm rather than inventing a plausible one.

```bash
S=skills/bibguard/scripts/bibguard.py

python3 $S references.bib --add "Attention Is All You Need"  # verify, then append
python3 $S references.bib                    # report (cached, safe to re-run)
python3 $S references.bib --fix              # write venues + one format back
python3 $S references.bib --refresh          # ignore the cache, re-query
python3 $S references.bib --uncited main.tex # entries the paper never cites
```

Exit code 0 means nothing to do and 1 means something needs attention, so it
drops straight into CI. Full flag reference, report format, sources and
`--fix` formatting rules: [`skills/bibguard/README.md`](skills/bibguard/README.md).

## iclr-paper-review

Reviews a paper as one scientific argument rather than a collection of keywords
and benchmark numbers:

- semantic novelty against the closest conceptual alternatives;
- a claim-to-evidence ledger across the main text and the appendix;
- an abstract audit for clarity, concision, coverage and detail control;
- a main-text self-containment gate, plus an individual audit of every figure
  and table and of its cross-references;
- a parameter, notation and equation ledger with type, shape, dimensional and
  logical checks;
- experimental sufficiency: baseline fairness, numerical clarity, generality,
  scale and reproducibility;
- an explicit appendix-length verdict, 20 pages targeted and 30 the hard maximum
  under the default rubric;
- writing, terminology, citation and narrative-logic review;
- one calibrated 1–10 score, with 8 reserved for Strong Accept;
- an optional, explicitly authorized iterative Git/Overleaf review loop.

Invoke it with a request such as:

```text
Use $iclr-paper-review to review this paper and its supplementary material, audit
every equation, figure and table, assess experimental sufficiency and appendix
length, and give one calibrated ICLR score.
```

The rubric and the specialized audit procedures live in
[`skills/iclr-paper-review/references/`](skills/iclr-paper-review/references/).

## paper-writing

The writing counterpart of the review skill: a per-section template for
producing the manuscript, and a linter for the measurable half of it.

- **Outline first.** No change to the paper, down to a word, without first
  checking and changing the outline. The outline carries a storyline with a
  claim-to-evidence table, and a link with no evidence is not written.
- **Conclusions follow the data.** A standing conclusion may be wrong; the
  idea and the headline claim can change, but the change lands in the outline
  first.
- Every sentence has a purpose and a source, nothing is said twice, and the
  shorter version wins. Edits go sentence by sentence, never as a wholesale
  rewrite, and a sentence the author wrote by hand stays verbatim.
- Written for a reader with no prior: terms of the field only, no coined
  nouns, every symbol and abbreviation defined before use, plain sentences
  without colons, and the register reviewers expect in each section.
- Numbers live in tables and come from generated macros; prose gives the
  direction of a result and the table it sits in. No bare numbers and no
  "Δ [lo, hi]" intervals in prose.
- A template per section: a five-step abstract, a three-paragraph
  introduction with three one-sentence contributions, one paragraph per
  category in related work, a framework figure in the method, and in the
  experiments a settings paragraph, one job per table, a two-block ablation,
  a qualitative figure chosen by eye and a cost table.
- Tables and figures: Base and +Method rows paired with the method's rows
  shaded, bold for the best per column, no N/A, small tables wrapped beside
  the text, a curve instead of a table where a quantity varies along an axis,
  and every caption opening with a one-sentence bold highlight.
- No code paths, script names or flags in the body. The appendix follows the
  order of the main text, opens each section by naming what it supplements,
  repeats a number only as the same macro, is at most 20 pages, starts on its
  own page under a title carrying the paper's own, and renumbers its floats
  per appendix section.
- Typesetting: the template's own fonts and spacing, no `\vspace`, caption
  skips set per float type, figure widths and trims measured rather than
  guessed, a page tightened by float separations, then `\bibsep`, then
  repeated sentences, and the main text filled to the last line of its page
  limit.

`paperlint` enforces what can be enforced and exits with the number of hard
failures:

```bash
python3 skills/paper-writing/scripts/paperlint.py main.tex --outline OUTLINE.md
```

HARD findings cover the outline gate, abstract length, introduction shape,
figure and table coverage, page limits and code paths in the body; WARN and INFO
cover the softer rules. It inlines `\input{}` so generated tables count, and
reads page counts from the compiled `.log`, `.aux` and PDF. The full rule table
is in [`skills/paper-writing/README.md`](skills/paper-writing/README.md), and the
rules themselves, in Chinese, are in
[`skills/paper-writing/SKILL.md`](skills/paper-writing/SKILL.md).

## Tests

Offline, no network and no key required:

```bash
python3 tests/test_skill_layout.py
python3 skills/bibguard/tests/test_offline.py
python3 skills/paper-writing/tests/test_offline.py
```
