#!/usr/bin/env python3
"""Offline structural checks for the two independent Agent Skills."""

from pathlib import Path
import re


ROOT = Path(__file__).resolve().parents[1]
EXPECTED = {"bibguard", "iclr-paper-review"}


def frontmatter(text: str):
    match = re.match(r"\A---\n(.*?)\n---\n", text, re.S)
    if not match:
        raise AssertionError("SKILL.md is missing YAML frontmatter")
    fields = {}
    for line in match.group(1).splitlines():
        if ":" in line and not line.startswith((" ", "\t")):
            key, value = line.split(":", 1)
            fields[key.strip()] = value.strip().strip('"')
    return fields


assert not (ROOT / "SKILL.md").exists(), "root SKILL.md hides nested skills"

skill_files = sorted((ROOT / "skills").glob("*/SKILL.md"))
folders = {path.parent.name for path in skill_files}
assert folders == EXPECTED, (folders, EXPECTED)

names = []
for path in skill_files:
    fields = frontmatter(path.read_text(encoding="utf-8"))
    assert fields.get("name") == path.parent.name, (path, fields.get("name"))
    assert fields.get("description"), f"missing description: {path}"
    names.append(fields["name"])

assert len(names) == len(set(names)), "duplicate skill names"

review_root = ROOT / "skills" / "iclr-paper-review"
for relative in (
    "references/review-rubric.md",
    "references/main-text-audit.md",
    "references/iterative-review-loop.md",
    "agents/openai.yaml",
):
    assert (review_root / relative).is_file(), f"missing {relative}"

bibguard_root = ROOT / "skills" / "bibguard"
for relative in ("scripts/bibguard.py", "scripts/venues.json", "tests/test_offline.py"):
    assert (bibguard_root / relative).is_file(), f"missing {relative}"

print("two independent skills validated: bibguard, iclr-paper-review")
