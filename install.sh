#!/usr/bin/env bash
# Install one or both independent research-paper skills.
#
#   bash install.sh                              # both, Codex, global
#   bash install.sh bibguard --codex --user
#   bash install.sh iclr-paper-review --claude /path/to/project
#   bash install.sh paper-writing --claude /path/to/project
#   bash install.sh all --claude --user
set -euo pipefail

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
SELECTED=all
AGENT=codex
PROJECT_DIR=""

usage() {
  sed -n '2,7p' "$0"
  cat <<'EOF'

Skills:  bibguard | iclr-paper-review | paper-writing | all
Agents:  --codex (default) | --claude
Scope:   --user (default) | /path/to/project
EOF
}

for arg in "$@"; do
  case "$arg" in
    bibguard|iclr-paper-review|paper-writing|all) SELECTED="$arg" ;;
    --all) SELECTED=all ;;
    --codex) AGENT=codex ;;
    --claude) AGENT=claude ;;
    --user) PROJECT_DIR="" ;;
    -h|--help) usage; exit 0 ;;
    -*) echo "Unknown option: $arg" >&2; usage >&2; exit 2 ;;
    *)
      [ -d "$arg" ] || { echo "No such directory: $arg" >&2; exit 1; }
      PROJECT_DIR="$(cd "$arg" && pwd)"
      ;;
  esac
done

if [ "$AGENT" = codex ]; then
  if [ -n "$PROJECT_DIR" ]; then
    DEST_ROOT="$PROJECT_DIR/.codex/skills"
  else
    DEST_ROOT="${CODEX_HOME:-$HOME/.codex}/skills"
  fi
else
  if [ -n "$PROJECT_DIR" ]; then
    DEST_ROOT="$PROJECT_DIR/.claude/skills"
  else
    DEST_ROOT="$HOME/.claude/skills"
  fi
fi

if [ "$SELECTED" = all ]; then
  SKILLS="bibguard iclr-paper-review paper-writing"
else
  SKILLS="$SELECTED"
fi

mkdir -p "$DEST_ROOT"

for skill_name in $SKILLS; do
  source_dir="$REPO_ROOT/skills/$skill_name"
  destination="$DEST_ROOT/$skill_name"
  [ -f "$source_dir/SKILL.md" ] || { echo "Invalid skill source: $source_dir" >&2; exit 1; }

  if [ -e "$destination" ]; then
    backup_path="$destination.bak.$(date +%Y%m%d%H%M%S)"
    echo "· Backing up existing $skill_name to $backup_path"
    mv "$destination" "$backup_path"
  fi

  cp -R "$source_dir" "$destination"
  [ -f "$destination/scripts/bibguard.py" ] && chmod +x "$destination/scripts/bibguard.py"

  if [ "$skill_name" = paper-writing ]; then
    command -v python3 >/dev/null || { echo "python3 is required for paper-writing" >&2; exit 1; }
    chmod +x "$destination/scripts/paperlint.py"
    python3 "$destination/tests/test_offline.py" >/dev/null
    echo "· paper-writing offline self-check passed"
  fi

  if [ "$skill_name" = bibguard ]; then
    command -v python3 >/dev/null || { echo "python3 is required for bibguard" >&2; exit 1; }
    python3 "$destination/tests/test_offline.py" >/dev/null
    echo "· bibguard offline self-check passed"
  fi

  echo "✅ Installed $skill_name to $destination"
done

cat <<EOF

Invoke the skills as \$bibguard, \$iclr-paper-review or \$paper-writing in a supported agent.
BibGuard CLI:  python3 $DEST_ROOT/bibguard/scripts/bibguard.py references.bib
paperlint CLI: python3 $DEST_ROOT/paper-writing/scripts/paperlint.py main.tex --outline OUTLINE.md
EOF
