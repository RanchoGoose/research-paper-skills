#!/usr/bin/env bash
# Install ref-verify as a Claude Code skill, into one project or globally.
#
#   bash install.sh /path/to/project   # -> that project's .claude/skills/
#   bash install.sh --user             # -> ~/.claude/skills/ (every project)
#   bash install.sh                    # no argument = --user
#
# Python 3 standard library only: no pip packages, no API key required.
set -euo pipefail

SRC="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
NAME=ref-verify

case "${1:---user}" in
  --user) DEST="$HOME/.claude/skills/$NAME" ;;
  -h|--help) sed -n '2,9p' "$0"; exit 0 ;;
  *)
    [ -d "$1" ] || { echo "No such directory: $1" >&2; exit 1; }
    DEST="$(cd "$1" && pwd)/.claude/skills/$NAME"
    ;;
esac

if [ "$SRC" = "$DEST" ]; then
  echo "Source and destination are the same directory; nothing to do."; exit 0
fi

command -v python3 >/dev/null || { echo "python3 is required" >&2; exit 1; }

mkdir -p "$(dirname "$DEST")"
if [ -d "$DEST" ]; then
  echo "· Already installed; backing up to $DEST.bak"
  rm -rf "$DEST.bak"; mv "$DEST" "$DEST.bak"
fi

mkdir -p "$DEST/scripts" "$DEST/tests"
for f in SKILL.md README.md LICENSE install.sh; do
  [ -f "$SRC/$f" ] && cp "$SRC/$f" "$DEST/"
done
cp "$SRC/scripts/verify_refs.py" "$SRC/scripts/venues.json" "$DEST/scripts/"
for f in test_offline.py sample.bib; do
  [ -f "$SRC/tests/$f" ] && cp "$SRC/tests/$f" "$DEST/tests/"
done
chmod +x "$DEST/scripts/verify_refs.py" "$DEST/install.sh" 2>/dev/null || true

# Self-check: a broken copy must fail here, not on someone's bibliography.
python3 "$DEST/tests/test_offline.py" >/dev/null 2>&1 \
  && echo "· self-check: offline tests pass" \
  || { echo "· self-check FAILED — run: python3 $DEST/tests/test_offline.py" >&2; exit 1; }

cat <<EOF
✅ Installed to $DEST

  python3 ${DEST/#$HOME/\~}/scripts/verify_refs.py references.bib
  python3 ${DEST/#$HOME/\~}/scripts/verify_refs.py references.bib --fix

Optional, for the widest venue coverage (free key from aminer.org):
  echo 'YOUR_KEY' > ~/.claude/aminer_key && chmod 600 ~/.claude/aminer_key

Add .refcache.json to .gitignore (it is written next to your .bib).
EOF
