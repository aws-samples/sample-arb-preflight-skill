#!/usr/bin/env bash
# Install the arb-preflight skill into an agent host.
#
#   ./install.sh kiro    [--global] [--dest DIR]   -> <workspace>/.kiro/skills/arb-preflight
#   ./install.sh claude  [--global] [--dest DIR]   -> <workspace>/.claude/skills/arb-preflight
#   ./install.sh quick   [--profile NAME]          -> dist/arb-preflight.zip (upload in Quick)
#   ./install.sh dir     --dest DIR                -> DIR/arb-preflight (any other host)
#
# --dest      workspace root for kiro/claude (default: current directory), or target dir for "dir"
# --global    install into the user-level skills folder (~/.kiro/skills or ~/.claude/skills)
# --profile   Amazon Quick desktop only: also copy into ~/.quickwork/profiles/NAME/skills
# --force     overwrite an existing install without asking
#
# Standard tools only (bash, cp, zip). Nothing is downloaded and nothing leaves the machine.
set -euo pipefail

SKILL_NAME="arb-preflight"
REPO_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
SRC="$REPO_DIR/skill/$SKILL_NAME"

usage() { sed -n '2,13p' "$0" | sed 's/^# \{0,1\}//'; exit "${1:-0}"; }

[[ $# -ge 1 ]] || usage 1
TARGET="$1"; shift
DEST=""; GLOBAL=0; PROFILE=""; FORCE=0
while [[ $# -gt 0 ]]; do
  case "$1" in
    --dest)    DEST="${2:?--dest needs a value}"; shift 2 ;;
    --global)  GLOBAL=1; shift ;;
    --profile) PROFILE="${2:?--profile needs a value}"; shift 2 ;;
    --force)   FORCE=1; shift ;;
    -h|--help) usage 0 ;;
    *) echo "Unknown option: $1" >&2; usage 1 ;;
  esac
done

[[ -f "$SRC/SKILL.md" ]] || { echo "Cannot find $SRC/SKILL.md" >&2; exit 1; }

copy_skill() {  # copy_skill <parent-dir>
  local parent="$1" target="$1/$SKILL_NAME"
  if [[ -e "$target" && $FORCE -eq 0 ]]; then
    read -r -p "$target exists. Overwrite? [y/N] " ans
    [[ "$ans" =~ ^[Yy]$ ]] || { echo "Skipped."; return 0; }
  fi
  mkdir -p "$parent"
  rm -rf "$target"
  # Copy the skill only; exclude OS clutter and any review output.
  (cd "$SRC/.." && tar --exclude='.DS_Store' --exclude='__pycache__' --exclude='reviews' -cf - "$SKILL_NAME") \
    | (cd "$parent" && tar -xf -)
  echo "Installed: $target"
}

case "$TARGET" in
  kiro|claude)
    dot=".$TARGET"
    if [[ $GLOBAL -eq 1 ]]; then base="$HOME/$dot/skills"; else base="${DEST:-$PWD}/$dot/skills"; fi
    copy_skill "$base"
    echo "Open the workspace in $TARGET and ask: Run an ARB pre-flight review on \"<file>.pptx\"."
    ;;
  quick)
    command -v zip >/dev/null || { echo "zip is required for the quick target" >&2; exit 1; }
    out="$REPO_DIR/dist"; mkdir -p "$out"; rm -f "$out/$SKILL_NAME.zip"
    (cd "$SRC/.." && zip -qr "$out/$SKILL_NAME.zip" "$SKILL_NAME" -x '*.DS_Store' '*__pycache__*' '*/reviews/*')
    echo "Built: $out/$SKILL_NAME.zip"
    echo "In Amazon Quick: Customize > Skills > Create > From file (choose the zip),"
    echo "or Create > From folder (choose $SRC). Then use 'Try it' to smoke-test."
    if [[ -n "$PROFILE" ]]; then
      copy_skill "$HOME/.quickwork/profiles/$PROFILE/skills"
      echo "Restart Amazon Quick desktop to pick up the skill."
    fi
    ;;
  dir)
    [[ -n "$DEST" ]] || { echo "dir target needs --dest DIR" >&2; exit 1; }
    copy_skill "$DEST"
    ;;
  *) echo "Unknown target: $TARGET" >&2; usage 1 ;;
esac
