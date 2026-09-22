# paper-writing

Writing rules for a research paper, and `paperlint`, the command that enforces
the measurable half of them. The rules (in `SKILL.md`, Chinese) are the
author's house style, written as a template that says what every paragraph of
every section is for: outline before prose, one idea per paragraph, every
sentence with a purpose and a source, only the field's own terms (no coined
nouns), numbers in tables and directions in prose, a fixed five-step abstract,
a three-paragraph introduction with three one-sentence contributions, one
distinct job per table with the method's rows shaded, captions that open with
the conclusion, an appendix that follows the order of the main text and only
supplements it, and a main text that ends on the last line of the page limit.
A section on typesetting covers what a reader sees before reading a word:
caption skips set per float type, figure widths and trims measured rather than
guessed, wrapped tables placed where they cannot fall off the page, and the
order to tighten a page in -- float separations, then `\bibsep`, and only then
a sentence.

```bash
python3 scripts/paperlint.py main.tex --outline OUTLINE.md
```

Exit code is the number of HARD findings. Standard library only, Python 3.8+.
`tests/test_offline.py` runs without LaTeX, git or network.

| Level | What fails |
|---|---|
| HARD | `main.tex` changed without `OUTLINE.md`; no storyline / claim-to-evidence table in the outline; a section the outline never mentions; abstract over 300 words; introduction under 3 paragraphs; fewer than 3 main-text figures, or none in Introduction / Related Work / Method; Experiments without a table; no ablation; main text over 9 pages; appendix over 20; a code path, script or flag in the body |
| WARN | abstract shape or detail; an acronym used before `Full Name (ACR)`; a math symbol with no defining sentence at first use; two sentences that say the same thing; a paragraph too long for one idea; a result literal in Experiments prose; `\appendix` without a preceding `\clearpage`; an appendix with no title, or a title that does not carry the paper's; appendix floats still numbered on the body's count; caption-above tables while `\belowcaptionskip` is never set non-zero |
| INFO | each section's opening sentence, to check it summarises the section |

It inlines `\input{}` so generated tables count. Page counts come from the
compiled `.log`, `.aux` and (if `pdftotext` is present) the PDF.
