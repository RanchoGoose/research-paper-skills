#!/usr/bin/env python3
"""Offline checks for paperlint: no network, no LaTeX, no git needed."""
import os
import subprocess
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
LINT = os.path.join(HERE, "..", "scripts", "paperlint.py")
OUTLINE = os.path.join(HERE, "sample_outline.md")


def run(tex, *extra):
    p = subprocess.run([sys.executable, LINT, os.path.join(HERE, tex), "--outline", OUTLINE,
                        "--no-git", *extra], capture_output=True, text=True)
    return p.returncode, p.stdout


rc, out = run("sample_good.tex")
hard = [l for l in out.splitlines() if l.startswith("HARD")]
assert rc == 0, (rc, out)
assert not hard, out
assert "abstract-length" in out and "Introduction: 3 paragraphs" in out, out

rc, out = run("sample_bad.tex")
codes = {l.split()[1] for l in out.splitlines() if l.startswith(("HARD", "WARN"))}
for want in ("abstract-length", "intro-shape", "figures-count", "figure-intro",
             "figure-related", "tables-count", "ablation", "code-ref",
             "acronym", "repeat", "number-in-prose", "outline-cover",
             "appendix-page", "appendix-title", "appendix-numbering",
             "caption-skip"):
    assert want in codes, (want, out)
assert rc >= 7, (rc, out)

# An appendix that opens on its own page under a heading, but a heading that
# says only "Appendix": a supplementary printed or reviewed on its own then
# cannot say which paper it belongs to. The title has to be the same macro the
# title page uses, or the two drift apart at the next edit.
STRAY = os.path.join(HERE, "_tmp_appendix_title.tex")
with open(STRAY, "w") as fh:
    fh.write(open(os.path.join(HERE, "sample_good.tex")).read()
             .replace("{\\large\\papertitle}\n", ""))
try:
    rc, out = run("_tmp_appendix_title.tex")
    assert "appendix-title" in out and "carry the paper" in out, out
    assert rc == 0, (rc, out)          # it is a WARN, not a HARD
finally:
    os.remove(STRAY)

# a missing outline is a hard failure, not a skipped check
p = subprocess.run([sys.executable, LINT, os.path.join(HERE, "sample_good.tex"),
                    "--outline", os.path.join(HERE, "nope.md"), "--no-git"],
                   capture_output=True, text=True)
assert p.returncode >= 1 and "outline" in p.stdout, p.stdout

print("paperlint offline checks passed")
