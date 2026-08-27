# paper-writing

Writing rules for a research paper, and `paperlint`, the command that enforces
the measurable half of them. The rules (in `SKILL.md`, Chinese) are the
author's house style: outline before prose, one idea per paragraph, every
sentence with a purpose and a source, every symbol defined before use, a fixed
four-part abstract, a three-paragraph introduction, a figure in each of the
first three sections, every result in a table, no code paths in the body, an
appendix of at most 20 pages.

```bash
python3 scripts/paperlint.py main.tex --outline OUTLINE.md
```

Exit code is the number of HARD findings. Standard library only, Python 3.8+.
`tests/test_offline.py` runs without LaTeX, git or network.

| Level | What fails |
|---|---|
| HARD | `main.tex` changed without `OUTLINE.md`; no storyline / claim-to-evidence table in the outline; a section the outline never mentions; abstract over 300 words; introduction under 3 paragraphs; fewer than 3 main-text figures, or none in Introduction / Related Work / Method; Experiments without a table; no ablation; main text over 9 pages; appendix over 20; a code path, script or flag in the body |
| WARN | abstract shape or detail; an acronym used before `Full Name (ACR)`; a math symbol with no defining sentence at first use; two sentences that say the same thing; a paragraph too long for one idea; a result literal in Experiments prose |
| INFO | each section's opening sentence, to check it summarises the section |

It inlines `\input{}` so generated tables count. Page counts come from the
compiled `.log`, `.aux` and (if `pdftotext` is present) the PDF.
