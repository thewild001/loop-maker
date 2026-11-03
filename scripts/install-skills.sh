#!/usr/bin/env bash
set -euo pipefail
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
TARGET="."
FORCE="${LOOP_MAKER_FORCE:-0}"
while [[ $# -gt 0 ]]; do
  case "$1" in
    --force) FORCE=1 ;;
    -h|--help)
      echo "Usage: bash scripts/install-skills.sh [--force] [target-directory]"
      echo "Default: preserve existing files; --force replaces Loop Maker-owned files."
      exit 0
      ;;
    *) TARGET="$1" ;;
  esac
  shift
done
mkdir -p "$TARGET"
copy_file() {
  local source="$1" destination="$2"
  mkdir -p "$(dirname "$destination")"
  if [[ -e "$destination" && "$FORCE" != "1" ]]; then
    echo "Preserved existing: $destination"
    return
  fi
  cp "$source" "$destination"
  echo "Installed: $destination"
}
copy_tree() {
  local source="$1" destination="$2" file relative
  mkdir -p "$destination"
  while IFS= read -r -d '' file; do
    relative="${file#"$source"/}"
    copy_file "$file" "$destination/$relative"
  done < <(find "$source" -type f -print0)
}
copy_tree "$ROOT/skills" "$TARGET/.agents/skills"
copy_tree "$ROOT/skills" "$TARGET/.claude/skills"
copy_tree "$ROOT/skills" "$TARGET/.opencode/skills"
copy_file "$ROOT/agents/loop-maker-orchestrator.md" "$TARGET/.opencode/agents/loop-maker-orchestrator.md"
copy_file "$ROOT/integrations/cursor/loop-maker.mdc" "$TARGET/.cursor/rules/loop-maker.mdc"
copy_file "$ROOT/integrations/copilot/loop-maker.instructions.md" "$TARGET/.github/instructions/loop-maker.instructions.md"
echo "Loop Maker skills installed into $TARGET"
