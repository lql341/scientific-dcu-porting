#!/usr/bin/env bash
# Install this skill into the local Codex / Claude Code skill directory.
#
#   ./install.sh              # user level (available in all projects)
#   ./install.sh --project    # .codex/skills/ or .claude/skills/ in this project
#   ./install.sh --codex      # force the Codex skill directory
#   ./install.sh --claude     # force the Claude Code skill directory
#   ./install.sh --link       # symlink (edits in the repo take effect immediately)
#
# Idempotent: an existing installation is moved to a timestamped backup first.

set -euo pipefail

SKILL_NAME="scientific-dcu-porting"
SRC_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"

MODE="user"
TARGET="auto"
LINK="no"
for arg in "$@"; do
    case "$arg" in
        --project) MODE="project" ;;
        --codex) TARGET="codex" ;;
        --claude) TARGET="claude" ;;
        --link)    LINK="yes" ;;
        -h|--help) sed -n '2,12p' "$0" | sed 's/^# \?//'; exit 0 ;;
        *) echo "unknown argument: $arg" >&2; exit 1 ;;
    esac
done

if [ "$TARGET" = "auto" ]; then
    if [ -n "${CODEX_HOME:-}" ] || [ -d "$HOME/.codex/skills" ]; then
        TARGET="codex"
    else
        TARGET="claude"
    fi
fi

if [ "$MODE" = "project" ]; then
    if [ "$TARGET" = "codex" ]; then
        DST_ROOT="$(pwd)/.codex/skills"
    else
        DST_ROOT="$(pwd)/.claude/skills"
    fi
elif [ "$TARGET" = "codex" ]; then
    DST_ROOT="${CODEX_HOME:-$HOME/.codex}/skills"
else
    DST_ROOT="${CLAUDE_CONFIG_DIR:-$HOME/.claude}/skills"
fi
DST="$DST_ROOT/$SKILL_NAME"

echo "==> source: $SRC_DIR"
echo "==> target: $DST ($TARGET)"

[ -f "$SRC_DIR/SKILL.md" ] || { echo "error: no SKILL.md in the source directory" >&2; exit 1; }

mkdir -p "$DST_ROOT"

if [ "$(cd "$DST" 2>/dev/null && pwd || echo -)" = "$SRC_DIR" ]; then
    echo "==> source and target are identical; nothing to do"
    exit 0
fi

if [ -e "$DST" ] || [ -L "$DST" ]; then
    backup="$DST.bak.$(date +%Y%m%d%H%M%S)"
    mv "$DST" "$backup"
    echo "==> existing install backed up as $(basename "$backup")"
fi

if [ "$LINK" = "yes" ]; then
    ln -s "$SRC_DIR" "$DST"
    echo "==> symlink created"
else
    mkdir -p "$DST"
    (cd "$SRC_DIR" && tar cf - --exclude='.git' --exclude='*.bak' \
        --exclude='__pycache__' .) | (cd "$DST" && tar xf -)
    chmod +x "$DST"/scripts/*.sh "$DST"/scripts/*.py 2>/dev/null || true
fi
echo "==> installed $SKILL_NAME"
