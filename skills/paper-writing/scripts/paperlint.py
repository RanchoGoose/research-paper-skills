#!/usr/bin/env python3
"""paperlint -- the mechanical half of the paper-writing skill.

The skill's rules are in SKILL.md. Most of them are judgement ("every sentence
has a purpose") and are enforced by reading. The ones that can be measured are
enforced here, so that a draft which breaks them fails a command rather than a
reviewer:

  outline     main.tex changed but OUTLINE.md did not; outline has no storyline
              ledger; a \\section the outline never mentions
  abstract    over the word budget; sentence count outside the fixed shape;
              carrying experimental detail
  intro       fewer than three paragraphs (background / problem / our approach)
  figures     fewer than three in the main text; Introduction, Related Work or
              Method without one
  tables      Experiments without a table; no ablation anywhere
  pages       appendix over its page budget; main text over its page budget
  acronyms    an abbreviation used before "Full Name (ABBR)" defines it
  symbols     a math symbol whose first use has no defining sentence nearby
  repeats     two sentences saying the same thing
  paragraphs  a paragraph too long to carry one idea
  numbers     a result literal in Experiments prose (must also be in a table)
  code-ref    a code path, script name or command-line flag in the main text

Exit code is the number of HARD findings. WARN and INFO never fail the run;
they are the list to read before deciding the draft is done.

    python3 paperlint.py main.tex --outline OUTLINE.md
    python3 paperlint.py main.tex --outline OUTLINE.md --json lint.json
    python3 paperlint.py main.tex --no-git          # outside a git checkout

Standard library only. Python 3.8+.
"""
from __future__ import annotations

import argparse
import json
import os
import re
import shutil
import subprocess
import sys
from typing import Dict, List, Optional, Tuple

HARD, WARN, INFO = "HARD", "WARN", "INFO"

# Abbreviations no reader needs defined. Deliberately short: the rule is that
# an abbreviation is defined before use, and a long whitelist is how that rule
# stops applying. Units and computing commonplaces only.
ACRONYMS_OK = {
    "GPU", "GPUS", "CPU", "CPUS", "RAM", "GB", "MB", "KB", "TB", "MS", "FPS",
    "ID", "IDS", "URL", "PDF", "API", "OS", "IO", "USD", "HTTP", "HTTPS",
    "AND", "OR", "NOT", "TODO", "FIXME", "II", "III", "IV", "VI", "VII",
    "VIII", "IX", "XI", "XII", "USA", "UK", "EU", "AM", "PM", "UTC",
}

# Words that end a sentence-ish token but are not sentence ends.
ABBREV_NO_STOP = {"e.g.", "i.e.", "cf.", "vs.", "et al.", "fig.", "eq.",
                  "sec.", "tab.", "app.", "no.", "approx.", "resp.", "w.r.t.",
                  "etc.", "al.", "st.", "dr.", "mr.", "ms.", "prof."}

GREEK = ("alpha", "beta", "gamma", "delta", "epsilon", "varepsilon", "zeta",
         "eta", "theta", "vartheta", "iota", "kappa", "lambda", "mu", "nu",
         "xi", "pi", "rho", "sigma", "tau", "upsilon", "phi", "varphi", "chi",
         "psi", "omega", "Gamma", "Delta", "Theta", "Lambda", "Xi", "Pi",
         "Sigma", "Upsilon", "Phi", "Psi", "Omega")

DEF_CUES = re.compile(
    r"(denote|let\b|where\b|\bis the\b|\bare the\b|\bbe the\b|:=|\\triangleq|"
    r"\\coloneqq|\bdefined?\b|\bwe write\b|\bwe call\b|\bstands? for\b|"
    r"\bnamely\b|\bi\.e\.)", re.I)


class Line:
    __slots__ = ("file", "no", "text")

    def __init__(self, file: str, no: int, text: str):
        self.file, self.no, self.text = file, no, text

    def where(self) -> str:
        return f"{self.file}:{self.no}"


# ---------------------------------------------------------------- reading

def strip_comment(s: str) -> str:
    out, i = [], 0
    while i < len(s):
        c = s[i]
        if c == "\\" and i + 1 < len(s):
            out.append(s[i:i + 2]); i += 2; continue
        if c == "%":
            break
        out.append(c); i += 1
    return "".join(out)


def read_tex(path: str, depth: int = 0, seen: Optional[set] = None) -> List[Line]:
    """Read a .tex file, inlining \\input{} and \\IfFileExists{f}{\\input{f}}.

    Inlining matters: tables and generated narrative often live in gen/*.tex,
    and a check that never sees them reports an Experiments section with no
    table. Missing files are skipped, matching what LaTeX's \\IfFileExists does.
    """
    seen = seen if seen is not None else set()
    real = os.path.realpath(path)
    if real in seen or depth > 6 or not os.path.isfile(path):
        return []
    seen.add(real)
    base = os.path.dirname(path)
    out: List[Line] = []
    with open(path, encoding="utf-8", errors="replace") as f:
        for no, raw in enumerate(f, 1):
            text = strip_comment(raw.rstrip("\n"))
            out.append(Line(path, no, text))
            for m in re.finditer(r"\\(?:input|include)\{([^}]+)\}", text):
                sub = m.group(1)
                if not sub.endswith(".tex"):
                    sub += ".tex"
                out.extend(read_tex(os.path.join(base, sub), depth + 1, seen))
    return out


# ---------------------------------------------------------------- structure

SECTION_RE = re.compile(r"\\(section|subsection|subsubsection)\*?\{")


def brace_arg(s: str, start: int) -> Tuple[str, int]:
    """Return the {...} argument starting at s[start] == '{' and its end."""
    depth, i = 0, start
    while i < len(s):
        if s[i] == "\\":
            i += 2; continue
        if s[i] == "{":
            depth += 1
        elif s[i] == "}":
            depth -= 1
            if depth == 0:
                return s[start + 1:i], i + 1
        i += 1
    return s[start + 1:], len(s)


class Section:
    def __init__(self, level: str, title: str, label: str, idx: int):
        self.level, self.title, self.label, self.idx = level, title, label, idx
        self.end = None  # exclusive

    def kind(self) -> str:
        t = detex(self.title).lower()
        if "introduction" in t:
            return "intro"
        if "related" in t or "background" in t or "prior work" in t:
            return "related"
        if re.search(r"\bmethod|approach|framework|proposed|model\b", t):
            return "method"
        if re.search(r"experiment|result|evaluation|empirical", t):
            return "experiments"
        if "conclusion" in t or "discussion" in t or "limitation" in t:
            return "conclusion"
        return "other"


def detex(s: str) -> str:
    """Plain words from a LaTeX fragment. Commands become one token each."""
    s = re.sub(r"\\(cite[pt]?|ref|eqref|label|autoref|cref|Cref|url|href|"
               r"includegraphics|input|bibliography\w*|hypersetup)\*?"
               r"(\[[^\]]*\])?\{[^}]*\}", " ", s)
    s = re.sub(r"\$\$.*?\$\$", " MATH ", s)
    s = re.sub(r"\$[^$]*\$", " MATH ", s)
    s = re.sub(r"\\\(.*?\\\)", " MATH ", s)
    s = re.sub(r"\\(emph|textbf|textit|texttt|textsc|underline|mbox|hbox|"
               r"footnote|caption|section\*?|subsection\*?|paragraph|"
               r"textcolor\{[^}]*\})\{", " {", s)
    s = re.sub(r"\\[a-zA-Z]+\*?", " CMD ", s)
    s = re.sub(r"[{}~]", " ", s)
    s = s.replace("---", " -- ").replace("--", " -- ")
    return re.sub(r"\s+", " ", s).strip()


def locate(lines: List[Line]) -> Dict:
    abstract = [None, None]
    sections: List[Section] = []
    appendix_at = None
    bib_at = None
    doc_end = len(lines)
    for i, ln in enumerate(lines):
        t = ln.text
        if r"\begin{abstract}" in t:
            abstract[0] = i
        if r"\end{abstract}" in t:
            abstract[1] = i
        if re.search(r"^\s*\\appendix\b", t) and appendix_at is None:
            appendix_at = i
        if re.search(r"\\bibliography\{", t) and bib_at is None:
            bib_at = i
        if r"\end{document}" in t:
            doc_end = i
            break
        for m in SECTION_RE.finditer(t):
            title, end = brace_arg(t, m.end() - 1)
            lab = re.search(r"\\label\{([^}]+)\}", t[end:])
            if not lab and i + 1 < len(lines):
                lab = re.search(r"^\s*\\label\{([^}]+)\}", lines[i + 1].text)
            sections.append(Section(m.group(1), title, lab.group(1) if lab else "", i))
    rank = {"section": 0, "subsection": 1, "subsubsection": 2}
    for k, a in enumerate(sections):
        a.end = doc_end
        for b in sections[k + 1:]:
            if rank[b.level] <= rank[a.level]:
                a.end = b.idx
                break
    main_end = min(x for x in (appendix_at, bib_at, doc_end) if x is not None)
    for s in sections:
        s.end = min(s.end, doc_end)
    return dict(abstract=abstract, sections=sections, appendix_at=appendix_at,
                bib_at=bib_at, main_end=main_end, doc_end=doc_end)


def env_mask(lines: List[Line], names=("table", "table*", "figure", "figure*",
                                       "wrapfigure", "wraptable", "tabular",
                                       "equation", "equation*", "align",
                                       "align*", "algorithm", "algorithmic",
                                       "lstlisting", "verbatim", "tikzpicture")) -> List[bool]:
    """True for lines inside a float / display-math / code environment."""
    inside = [False] * len(lines)
    depth = 0
    for i, ln in enumerate(lines):
        t = ln.text
        opens = len([m for m in re.finditer(r"\\begin\{([^}]+)\}", t) if m.group(1) in names])
        closes = len([m for m in re.finditer(r"\\end\{([^}]+)\}", t) if m.group(1) in names])
        if depth > 0 or opens:
            inside[i] = True
        depth = max(0, depth + opens - closes)
    return inside


# ---------------------------------------------------------------- text units

def sentences(text: str) -> List[str]:
    """Crude sentence split that survives 'e.g.' and 'Fig. 3'."""
    out, buf = [], []
    for tok in text.split():
        buf.append(tok)
        low = tok.lower()
        if low[-1:] in ".!?" and low not in ABBREV_NO_STOP and not re.match(r"^[a-z]\.$", low) \
                and not re.match(r"^\d+\.$", low):
            out.append(" ".join(buf)); buf = []
    if buf:
        out.append(" ".join(buf))
    return [s for s in out if len(s.split()) >= 2]


def paragraphs(lines: List[Line], lo: int, hi: int, mask: List[bool]) -> List[Tuple[int, int, str]]:
    """(start, end, text) of prose paragraphs in lines[lo:hi], floats excluded."""
    out, buf, start = [], [], None
    for i in range(lo, hi):
        t = lines[i].text.strip()
        skip = mask[i] or t.startswith("\\") and re.match(
            r"\\(section|subsection|subsubsection|label|vspace|input|include|"
            r"IfFileExists|begin|end|centering|newcommand|renewcommand|"
            r"setlength|item|bibliography|bibliographystyle|appendix|"
            r"clearpage|newpage|noindent|maketitle|hypersetup|setcounter)", t)
        if not t or skip:
            if buf:
                out.append((start, i, " ".join(buf))); buf = []
            continue
        if start is None or not buf:
            start = i
        buf.append(t)
    if buf:
        out.append((start, hi, " ".join(buf)))
    return out


# ---------------------------------------------------------------- findings

class Report:
    def __init__(self):
        self.items: List[Dict] = []

    def add(self, level: str, code: str, where: str, msg: str):
        self.items.append(dict(level=level, code=code, where=where, msg=msg))

    def hard(self) -> int:
        return sum(1 for x in self.items if x["level"] == HARD)


# ---------------------------------------------------------------- checks

def check_outline(lines, S, args, R: Report):
    if not args.outline:
        R.add(WARN, "outline", args.tex, "no --outline given: the outline-first rule was not checked")
        return
    if not os.path.isfile(args.outline):
        R.add(HARD, "outline", args.outline, "outline file does not exist -- write it before the paper")
        return
    outline = open(args.outline, encoding="utf-8", errors="replace").read()

    # (a) The paper changed; did the outline?
    if not args.no_git:
        try:
            st = subprocess.run(["git", "status", "--porcelain", "--", args.tex, args.outline],
                                capture_output=True, text=True, timeout=20,
                                cwd=os.path.dirname(os.path.abspath(args.tex)) or ".")
            if st.returncode == 0:
                dirty = {l[3:].strip() for l in st.stdout.splitlines() if l.strip()}
                tex_dirty = any(os.path.basename(d) == os.path.basename(args.tex) for d in dirty)
                out_dirty = any(os.path.basename(d) == os.path.basename(args.outline) for d in dirty)
                if tex_dirty and not out_dirty:
                    R.add(HARD, "outline-first", args.tex,
                          f"{os.path.basename(args.tex)} is modified but {os.path.basename(args.outline)} "
                          "is not -- change the outline first, then the paper")
        except (OSError, subprocess.SubprocessError):
            R.add(WARN, "outline-first", args.tex, "git not available; outline-first not checked")

    # (b) A storyline with evidence per link.
    story = re.search(r"^#{1,4}\s.*?(故事线|storyline|story\s*line)", outline, re.I | re.M)
    if not story:
        R.add(HARD, "outline-story", args.outline,
              "outline has no '故事线 / storyline' heading -- the story is written before the paper")
    elif not re.search(r"^\|.*(证据|evidence|依据).*\|\s*$", outline[story.start():], re.I | re.M):
        R.add(HARD, "outline-ledger", args.outline,
              "no claim-to-evidence table under the storyline heading (a header row containing "
              "证据/evidence) -- every link of the story names its evidence")

    # (c) Every main-text section is somewhere in the outline.
    low = outline.lower()
    for s in S["sections"]:
        if s.idx >= S["main_end"]:
            break
        title = detex(s.title).lower()
        hit = (s.label and s.label.lower() in low) or (title and title in low) \
            or (title and all(w in low for w in title.split() if len(w) > 3))
        if not hit:
            lvl = HARD if s.level == "section" else WARN
            R.add(lvl, "outline-cover", lines[s.idx].where(),
                  f"\\{s.level} '{detex(s.title)}' ({s.label or 'no label'}) appears nowhere in the outline")


def check_abstract(lines, S, args, R: Report):
    a, b = S["abstract"]
    if a is None or b is None:
        R.add(HARD, "abstract", args.tex, "no \\begin{abstract} ... \\end{abstract}")
        return
    raw = " ".join(l.text for l in lines[a + 1:b])
    plain = detex(raw)
    words = [w for w in plain.split() if re.search(r"[A-Za-z0-9]", w)]
    sents = sentences(plain)
    where = lines[a].where()
    if len(words) > args.max_abstract_words:
        R.add(HARD, "abstract-length", where,
              f"abstract is {len(words)} words; budget {args.max_abstract_words}")
    else:
        R.add(INFO, "abstract-length", where, f"abstract: {len(words)} words, {len(sents)} sentences")
    if not (9 <= len(sents) <= 17):
        R.add(WARN, "abstract-shape", where,
              f"{len(sents)} sentences; the fixed shape is 3-5 background + 2 problem + "
              "2-5 method/contribution + 2-5 findings = 9-17")
    detail = len(re.findall(r"\bMATH\b", plain)) + len(re.findall(r"\bCMD\b", plain)) \
        + len(re.findall(r"\b\d+(?:\.\d+)?%?\b", plain))
    if detail > 4:
        R.add(WARN, "abstract-detail", where,
              f"{detail} numbers/macros/math tokens in the abstract -- findings there are "
              "high-level; leave the estimates and intervals to the tables")


def check_intro(lines, S, args, R: Report, mask):
    intro = next((s for s in S["sections"] if s.kind() == "intro"), None)
    if not intro:
        R.add(WARN, "intro", args.tex, "no Introduction section found (by title)")
        return
    paras = paragraphs(lines, intro.idx + 1, min(intro.end, S["main_end"]), mask)
    n = len(paras)
    where = lines[intro.idx].where()
    if n < 3:
        R.add(HARD, "intro-shape", where,
              f"Introduction has {n} paragraphs; needs background / the problem / our approach "
              "+ contributions")
    elif n > 6:
        R.add(WARN, "intro-shape", where,
              f"Introduction has {n} paragraphs; the shape is three (background, problem, our "
              "approach) plus the contribution list")
    else:
        R.add(INFO, "intro-shape", where, f"Introduction: {n} paragraphs")


def figures_in(lines, lo, hi) -> int:
    n = 0
    for i in range(lo, hi):
        n += len(re.findall(r"\\begin\{(?:figure\*?|wrapfigure)\}", lines[i].text))
    return n


def tables_in(lines, lo, hi) -> int:
    n = 0
    for i in range(lo, hi):
        n += len(re.findall(r"\\begin\{(?:table\*?|wraptable)\}", lines[i].text))
    return n


def check_figures(lines, S, args, R: Report):
    total = figures_in(lines, 0, S["main_end"])
    if total < args.min_figures:
        R.add(HARD, "figures-count", args.tex,
              f"{total} figure(s) in the main text; at least {args.min_figures} are required")
    else:
        R.add(INFO, "figures-count", args.tex, f"{total} figures in the main text")
    want = {"intro": "Introduction", "related": "Related Work", "method": "Method"}
    seen = set()
    for s in S["sections"]:
        if s.level != "section" or s.idx >= S["main_end"]:
            continue
        k = s.kind()
        if k in want and k not in seen:
            seen.add(k)
            n = figures_in(lines, s.idx, min(s.end, S["main_end"]))
            if n == 0:
                R.add(HARD, "figure-" + k, lines[s.idx].where(),
                      f"{want[k]} has no figure (a small one is fine; Method's must show the whole framework)")
    for k, name in want.items():
        if k not in seen:
            R.add(WARN, "figure-" + k, args.tex, f"no section titled like '{name}' found; its figure rule not checked")


def check_tables(lines, S, args, R: Report):
    exp = [s for s in S["sections"] if s.level == "section" and s.kind() == "experiments"
           and s.idx < S["main_end"]]
    if not exp:
        R.add(WARN, "tables", args.tex, "no Experiments/Results section found (by title)")
    else:
        n = sum(tables_in(lines, s.idx, min(s.end, S["main_end"])) for s in exp)
        if n == 0:
            R.add(HARD, "tables-count", lines[exp[0].idx].where(),
                  "Experiments has no table; every result is stated in a table")
        else:
            R.add(INFO, "tables-count", lines[exp[0].idx].where(), f"Experiments: {n} table(s)")
    body = " ".join(l.text for l in lines[:S["main_end"]]).lower()
    if "ablat" not in body:
        R.add(HARD, "ablation", args.tex,
              "no ablation in the main text (no 'ablation' in any title, caption or paragraph)")


def check_pages(lines, S, args, R: Report):
    stem = os.path.splitext(args.tex)[0]
    log = args.log or stem + ".log"
    aux = args.aux or stem + ".aux"
    total = None
    if os.path.isfile(log):
        m = re.search(r"Output written on .*?\((\d+) pages?", open(log, encoding="utf-8", errors="replace").read())
        if m:
            total = int(m.group(1))
    if total is None:
        R.add(WARN, "pages", log, "no compiled .log with a page count; compile before the gate")
        return
    app_start = None
    if os.path.isfile(aux):
        for m in re.finditer(r"contentsline \{section\}\{\\numberline \{([A-Z])\}.*?\}\{(\d+)\}",
                             open(aux, encoding="utf-8", errors="replace").read()):
            app_start = int(m.group(2)); break
    if S["appendix_at"] is not None:
        if app_start is None:
            R.add(WARN, "pages-appendix", aux, "\\appendix present but its first page not found in .aux")
        else:
            n = total - app_start + 1
            lvl = HARD if n > args.max_appendix_pages else INFO
            R.add(lvl, "pages-appendix", aux,
                  f"appendix is {n} pages (p{app_start}-{total}); budget {args.max_appendix_pages}"
                  + ("" if lvl == INFO else " -- the appendix supplements; the paper must be complete without it"))
    pdf = stem + ".pdf"
    if shutil.which("pdftotext") and os.path.isfile(pdf):
        ref_page = None
        for p in range(1, total + 1):
            try:
                txt = subprocess.run(["pdftotext", "-f", str(p), "-l", str(p), "-layout", pdf, "-"],
                                     capture_output=True, text=True, timeout=30).stdout
            except (OSError, subprocess.SubprocessError):
                break
            # review styles print a line number at the left of every line
            head = [re.sub(r"^\d+\s*", "", l.strip()) for l in txt.splitlines() if l.strip()]
            head = [l for l in head if l][:60]
            # The main text ends where the first back-matter heading begins:
            # References, or an Ethics / Reproducibility statement placed
            # before them. Small-caps headings extract with a space after the
            # capital ("R EFERENCES"), so letters may be separated by spaces.
            for j, l in enumerate(head):
                flat = re.sub(r"\s+", "", l).upper()
                if flat in ("REFERENCES", "BIBLIOGRAPHY", "ETHICSSTATEMENT",
                            "REPRODUCIBILITYSTATEMENT", "ACKNOWLEDGMENTS", "ACKNOWLEDGEMENTS"):
                    ref_page = (p, j); break
            if ref_page:
                break
        if ref_page:
            p, j = ref_page
            if p <= args.max_main_pages or (p == args.max_main_pages + 1 and j <= 2):
                R.add(INFO, "pages-main", pdf, f"back matter begins on p{p}; main text within {args.max_main_pages} pages")
            else:
                R.add(HARD, "pages-main", pdf,
                      f"back matter begins on p{p} (line {j+1} of the page): main text exceeds "
                      f"{args.max_main_pages} pages -- cut repetition, never facts or tables")
        else:
            R.add(WARN, "pages-main", pdf, "could not find the References heading; main-text length not checked")
    else:
        R.add(WARN, "pages-main", pdf, "pdftotext or the PDF is missing; main-text length not checked")


PROTECTED_ARGS = re.compile(
    r"\\(cite[pt]?|citeauthor|ref|eqref|autoref|cref|Cref|label|url|href|texttt|"
    r"includegraphics|input|include|bibliography\w*|hypersetup|newcommand|"
    r"renewcommand|providecommand|IfFileExists|usepackage|documentclass|"
    r"pol|method)\*?(\[[^\]]*\])?\{[^}]*\}")


def prose_only(t: str) -> str:
    t = PROTECTED_ARGS.sub(" ", t)
    t = re.sub(r"\$\$.*?\$\$", " ", t)
    t = re.sub(r"\$[^$]*\$", " ", t)
    return t


def check_acronyms(lines, S, args, R: Report, mask):
    ok = set(ACRONYMS_OK)
    if args.acronyms_ok and os.path.isfile(args.acronyms_ok):
        ok |= {w.strip().upper() for w in open(args.acronyms_ok) if w.strip() and not w.startswith("#")}
    first: Dict[str, int] = {}
    defined: Dict[str, int] = {}
    order = []
    for i in range(0, S["main_end"]):
        if mask[i] and not re.search(r"\\caption", lines[i].text):
            continue
        if MACRO_DEF.search(lines[i].text):
            continue
        t = prose_only(lines[i].text)
        for m in re.finditer(r"\(\s*([A-Z][A-Z0-9]{1,7})s?\s*\)", t):      # Full Name (ABBR)
            defined.setdefault(m.group(1), i)
        for m in re.finditer(r"\b([A-Z][A-Z0-9]{1,7})s?\s*\(", t):          # ABBR (Full Name)
            defined.setdefault(m.group(1), i)
        for m in re.finditer(r"\\(?:gls|acrshort|acrfull|ac|acf)\{([^}]+)\}", t):
            defined.setdefault(m.group(1).upper(), -1)
        for m in re.finditer(r"(?<![\w\\{])([A-Z][A-Z0-9]{1,7})s?(?![\w}])", t):
            w = m.group(1)
            if w in ok or w.isdigit() or len(w) < 2:
                continue
            if w not in first:
                first[w] = i; order.append(w)
    for w in order:
        d = defined.get(w)
        if d is None or d > first[w] + 1:
            R.add(WARN, "acronym", lines[first[w]].where(),
                  f"'{w}' used before it is defined as 'Full Name ({w})'"
                  + (f" (defined later at {lines[d].where()})" if d is not None and d >= 0 else ""))


MACRO_DEF = re.compile(r"\\(newcommand|renewcommand|providecommand|def|DeclareMathOperator|newacronym)\b")


def check_symbols(lines, S, args, R: Report, mask):
    first: Dict[str, int] = {}
    order = []
    display_math = env_mask(lines, names=("equation", "equation*", "align", "align*",
                                          "gather", "gather*", "multline"))
    for i in range(0, S["main_end"]):
        t = lines[i].text
        if MACRO_DEF.search(t):
            continue                      # a definition is not a use
        if mask[i] and not re.search(r"\\caption|\\begin\{(equation|align)", t) \
                and not display_math[i]:
            continue                      # figure internals: judged with the figure
        maths = re.findall(r"\$\$(.*?)\$\$|\$([^$]*)\$", t)
        if display_math[i]:
            maths.append(("", t))
        for m in maths:
            frag = m[0] or m[1]
            for s in re.findall(r"\\(?:mathcal|mathbf|boldsymbol|mathbb|mathrm|mathsf)\{([A-Za-z])\}", frag):
                key = s
                if key not in first:
                    first[key] = i; order.append(key)
            for g in re.findall(r"\\(" + "|".join(GREEK) + r")\b", frag):
                key = "\\" + g
                if key not in first:
                    first[key] = i; order.append(key)
    for key in order:
        i = first[key]
        ctx = " ".join(lines[k].text for k in range(max(0, i - 2), min(len(lines), i + 3)))
        if not DEF_CUES.search(ctx):
            R.add(WARN, "symbol", lines[i].where(),
                  f"symbol '{key}' first appears here with no defining phrase nearby "
                  "(denote / let / where / is the / :=)")


def norm_tokens(s: str) -> List[str]:
    s = detex(s).lower()
    return [w for w in re.findall(r"[a-z][a-z\-]+", s) if w not in ("math", "cmd")]


def check_repeats(lines, S, args, R: Report, mask):
    units = []  # (line index, tokens)
    inside = env_mask(lines, names=("tabular", "equation", "equation*", "align", "align*",
                                    "algorithm", "algorithmic", "lstlisting", "verbatim", "tikzpicture"))
    for st, en, text in paragraphs(lines, 0, S["main_end"], inside):
        for sent in sentences(text):
            toks = norm_tokens(sent)
            if len(toks) >= 9:
                units.append((st, toks, sent))
    shingles = []
    for st, toks, sent in units:
        shingles.append(set(" ".join(toks[k:k + 3]) for k in range(len(toks) - 2)))
    seen_pairs = 0
    for a in range(len(units)):
        A = shingles[a]
        if not A:
            continue
        for b in range(a + 1, len(units)):
            B = shingles[b]
            if not B or units[a][0] == units[b][0]:
                continue
            inter = len(A & B)
            if inter == 0:
                continue
            j = inter / len(A | B)
            if j >= 0.5:
                seen_pairs += 1
                if seen_pairs <= 40:
                    R.add(WARN, "repeat", lines[units[a][0]].where(),
                          f"says the same as line {lines[units[b][0]].no} (overlap {j:.2f}): "
                          f"\"{units[a][2][:90]}...\"")
    if seen_pairs > 40:
        R.add(WARN, "repeat", args.tex, f"{seen_pairs - 40} more repeated-sentence pairs not listed")


def check_paragraphs(lines, S, args, R: Report, mask):
    for s in S["sections"]:
        if s.idx >= S["main_end"] or s.level != "section":
            continue
        paras = paragraphs(lines, s.idx + 1, min(s.end, S["main_end"]), mask)
        # the first paragraph of a section states what the section does
        body = [p for p in paras if not re.match(r"\\(begin|end)\{", p[2])]
        if body:
            first = sentences(detex(body[0][2]))
            if first:
                R.add(INFO, "section-lead", lines[body[0][0]].where(),
                      f"'{detex(s.title)}' opens: \"{first[0][:110]}\" -- does it summarise the section?")
        for st, en, text in paras:
            n = len(sentences(detex(text)))
            w = len(detex(text).split())
            if n > 10 or w > 260:
                R.add(WARN, "paragraph", lines[st].where(),
                      f"paragraph of {n} sentences / {w} words: one idea per paragraph -- "
                      "if it cannot be summarised in one line, split it")


def check_numbers(lines, S, args, R: Report, mask):
    exp = [s for s in S["sections"] if s.level == "section" and s.kind() == "experiments"
           and s.idx < S["main_end"]]
    for s in exp:
        for st, en, text in paragraphs(lines, s.idx + 1, min(s.end, S["main_end"]), mask):
            plain = prose_only(text)
            nums = re.findall(r"(?<![\w.])(?<!\w-)[-+]?\d+\.\d+(?![\w.-])|\b\d+(?:\.\d+)?%", plain)
            if nums:
                R.add(WARN, "number-in-prose", lines[st].where(),
                      f"result literal(s) in prose: {', '.join(nums[:6])}"
                      + (" ..." if len(nums) > 6 else "") + " -- confirm a table carries them")


CODE_REF = re.compile(
    r"\\texttt\{[^}]*(?:/|\.py|\.sh|\.json|\.tex|--)[^}]*\}"      # \texttt{code/x.py --flag}
    r"|(?<![\w\\])(?:code|scripts?|src)/[\w./\\-]+"                  # code/check_gen.sh
    r"|\b[\w\\-]+\.(?:py|sh|ipynb|yaml|yml|json|csv)\b"               # paired_stats.py
    r"|(?<![\w-])--[a-z][\w-]+\b")                                   # --audit


def check_code_refs(lines, S, args, R: Report, mask):
    """The main text argues from results, not from the tooling that produced them.

    A sentence such as "code/check_gen.sh regenerates and diffs them" belongs in
    the repository README, not in the paper: it tells the reader nothing about
    the claim, and the reader has no way to act on it. Code paths, script names
    and command-line flags are therefore forbidden in the body. Reproducibility
    statements name the release, not its file listing.
    """
    n = 0
    for i in range(0, S["main_end"]):
        if mask[i] and not re.search(r"\\caption", lines[i].text):
            continue
        t = lines[i].text
        if MACRO_DEF.search(t) or re.search(r"\\(input|include|includegraphics|IfFileExists|bibliography\w*)\{", t):
            continue
        t = re.sub(r"\$[^$]*\$", " ", t)
        hits = [m.group(0) for m in CODE_REF.finditer(t)]
        if hits:
            n += 1
            if n <= 30:
                R.add(HARD, "code-ref", lines[i].where(),
                      "code reference in the main text: " + "; ".join(h[:60] for h in hits[:4]))
    if n > 30:
        R.add(HARD, "code-ref", args.tex, f"{n - 30} more lines with code references not listed")


# ---------------------------------------------------------------- layout

def _newcommands(lines: List[Line]) -> Dict[str, str]:
    """{macro name -> body} for one-argument \newcommand definitions."""
    out = {}
    for ln in lines:
        for m in re.finditer(r"\\(?:new|renew|provide)command\*?\s*\{?\\([A-Za-z]+)\}?\s*(?=\{)", ln.text):
            body, _ = brace_arg(ln.text, ln.text.index("{", m.end() - 1))
            out[m.group(1)] = body
    return out


def _expand(s: str, macros: Dict[str, str], depth: int = 3) -> str:
    for _ in range(depth):
        new = re.sub(r"\\([A-Za-z]+)\b", lambda m: macros.get(m.group(1), m.group(0)), s)
        if new == s:
            break
        s = new
    return s


def _words(s: str) -> List[str]:
    return [w for w in re.findall(r"[A-Za-z]{3,}", detex(s).lower()) if w != "cmd"]


def check_layout(lines, S, args, R: Report):
    r"""Three things the eye catches on a printed page and no other check sees.

    **The appendix has to start on its own page, under its own title.** Left to
    itself it starts wherever the reference list happens to stop -- often a few
    entries down a page it shares with the bibliography -- and the first
    appendix section then reads as a continuation of the references. The title
    should carry the paper's title as well as the word "Appendix": a
    supplementary that gets printed, downloaded or reviewed on its own has to
    say what it belongs to. Take it from the same macro `\title` uses, or the
    two drift apart the next time either is edited.

    **A caption above a table needs \belowcaptionskip.** Table captions
    conventionally sit above the tabular and figure captions below the graphic,
    so one pair of caption skips means opposite things to the two float types
    and no single global setting serves both. `article` ships 10pt above and
    **0pt below**, which on a caption-above table rests the caption's last line
    directly on the top rule while \textfloatsep still separates the table from
    the text under it -- the caption ends up looking further from its own table
    than the table is from the next paragraph. Setting the pair per float type
    (at \begin{table} and \begin{figure}, inside the float's own group, so
    neither leaks into the other) is the fix.

    **Appendix floats are numbered under their appendix section**, A.1 and C.2
    rather than continuing the body's count into Figure 7 and Table 18. A
    number that continues the body's sequence tells the reader nothing about
    where to look: they have to count eighteen tables forward through material
    whose sections are lettered, not numbered. \counterwithin{figure}{section}
    after \appendix does both halves -- the prefix and a reset at every
    section -- so the two numbering systems cannot collide.
    """
    macros = _newcommands(lines)

    ap = S.get("appendix_at")
    if ap is not None:
        head = "\n".join(lines[i].text for i in range(max(0, ap - 6), ap))
        if not re.search(r"\\(clearpage|newpage|cleardoublepage)\b", head):
            R.add(WARN, "appendix-page", lines[ap].where(),
                  r"\appendix is not preceded by \clearpage: the appendix will start "
                  r"wherever the reference list happens to stop")
        stop = min([s.idx for s in S["sections"] if s.idx > ap] or [len(lines)])
        block = "\n".join(lines[i].text for i in range(ap, stop))
        if not re.search(r"Appendix|APPENDIX", _expand(block, macros)):
            R.add(WARN, "appendix-title", lines[ap].where(),
                  "no title between \\appendix and its first section -- the appendix "
                  "opens with no heading of its own")
        else:
            title = ""
            for ln in lines:
                m = re.search(r"\\title\s*(?=\{)", ln.text)
                if m:
                    title, _ = brace_arg(ln.text, ln.text.index("{", m.end() - 1))
                    break
            tw = set(_words(_expand(title, macros)))
            bw = set(_words(_expand(block, macros)))
            if tw and len(tw & bw) < max(2, len(tw) // 3):
                R.add(WARN, "appendix-title", lines[ap].where(),
                      "the appendix title does not carry the paper's title -- a "
                      "supplementary read on its own cannot say what it belongs to")

        tail = "\n".join(lines[i].text for i in range(ap, len(lines)))
        unnumbered = []
        for kind in ("figure", "table"):
            if not re.search(r"\\begin\{" + kind + r"\*?\}", tail):
                continue
            if not (re.search(r"\\counterwithin\*?\s*\{" + kind + r"\}", tail)
                    or re.search(r"\\(renew|provide)command\*?\s*\{?\\the" + kind + r"\}?", tail)
                    or re.search(r"\\@addtoreset\s*\{" + kind + r"\}", tail)):
                unnumbered.append(kind)
        if unnumbered:
            R.add(WARN, "appendix-numbering", lines[ap].where(),
                  " and ".join(unnumbered) + " numbering continues the main text's count "
                  r"into the appendix -- use \counterwithin{" + unnumbered[0] +
                  "}{section} so an appendix float is numbered under its own section "
                  "(A.1, C.2) and the number says which appendix to open")

    above = 0
    for i, ln in enumerate(lines):
        if r"\begin{table}" not in ln.text:
            continue
        chunk = ""
        for j in range(i, min(i + 60, len(lines))):
            chunk += lines[j].text + "\n"
            if r"\end{table}" in lines[j].text:
                break
        c, t = chunk.find(r"\caption"), chunk.find(r"\begin{tabular}")
        if c >= 0 and t >= 0 and c < t:
            above += 1
    if above:
        src = "\n".join(ln.text for ln in lines)
        # Any non-zero setting counts, however it is spelled: a literal
        # \setlength, a \captionsetup, or -- the form that actually gets used
        # once the two float types need different values -- a length register
        # the float hooks copy in, whose own \setlength is somewhere else
        # entirely. Resolve one level of that indirection rather than reporting
        # a paper that has already done the right thing.
        vals = []
        for raw in re.findall(r"belowcaptionskip\}?\s*\{([^}]*)\}", src):
            raw = raw.strip()
            m = re.match(r"([0-9.]+)\s*pt", raw)
            if m:
                vals.append(float(m.group(1)))
                continue
            m = re.match(r"\\([A-Za-z]+)$", raw)
            if m:
                vals += [float(v) for v in
                         re.findall(r"\\" + m.group(1) + r"\}?\s*\{\s*([0-9.]+)\s*pt", src)]
        vals += [float(v) for v in re.findall(r"belowskip\s*=\s*([0-9.]+)\s*pt", src)]
        if not vals or all(v == 0 for v in vals):
            R.add(WARN, "caption-skip", args.tex,
                  f"{above} table(s) put the caption above the tabular but "
                  r"\belowcaptionskip is never set to a non-zero length: the caption "
                  r"will touch the top rule while \textfloatsep separates the table "
                  "from the text below it")


# ---------------------------------------------------------------- main

def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description="mechanical gate for the paper-writing skill")
    ap.add_argument("tex")
    ap.add_argument("--outline", help="OUTLINE.md (the outline-first gate)")
    ap.add_argument("--log", help="LaTeX .log (default: <tex>.log)")
    ap.add_argument("--aux", help="LaTeX .aux (default: <tex>.aux)")
    ap.add_argument("--max-abstract-words", type=int, default=300)
    ap.add_argument("--max-appendix-pages", type=int, default=20)
    ap.add_argument("--max-main-pages", type=int, default=9)
    ap.add_argument("--min-figures", type=int, default=3)
    ap.add_argument("--acronyms-ok", help="file of abbreviations that need no definition, one per line")
    ap.add_argument("--no-git", action="store_true", help="skip the git-based outline-first check")
    ap.add_argument("--json", help="write findings here")
    ap.add_argument("--quiet-info", action="store_true", help="do not print INFO lines")
    args = ap.parse_args(argv)

    if not os.path.isfile(args.tex):
        print(f"no such file: {args.tex}", file=sys.stderr)
        return 99
    lines = read_tex(args.tex)
    S = locate(lines)
    mask = env_mask(lines)
    R = Report()

    check_outline(lines, S, args, R)
    check_abstract(lines, S, args, R)
    check_intro(lines, S, args, R, mask)
    check_figures(lines, S, args, R)
    check_tables(lines, S, args, R)
    check_pages(lines, S, args, R)
    check_acronyms(lines, S, args, R, mask)
    check_symbols(lines, S, args, R, mask)
    check_repeats(lines, S, args, R, mask)
    check_paragraphs(lines, S, args, R, mask)
    check_numbers(lines, S, args, R, mask)
    check_code_refs(lines, S, args, R, mask)
    check_layout(lines, S, args, R)

    rank = {HARD: 0, WARN: 1, INFO: 2}
    for it in sorted(R.items, key=lambda x: (rank[x["level"]], x["code"])):
        if it["level"] == INFO and args.quiet_info:
            continue
        print(f"{it['level']:4s} {it['code']:16s} {it['where']}: {it['msg']}")
    n_hard = R.hard()
    n_warn = sum(1 for x in R.items if x["level"] == WARN)
    print(f"== paperlint: {n_hard} hard, {n_warn} warn "
          f"({sum(1 for x in S['sections'] if x.level == 'section' and x.idx < S['main_end'])} "
          f"main-text sections, main text ends at line {lines[S['main_end']-1].no if lines else 0})")
    if args.json:
        json.dump(dict(hard=n_hard, warn=n_warn, findings=R.items), open(args.json, "w"), indent=1)
    return n_hard


if __name__ == "__main__":
    sys.exit(main())
