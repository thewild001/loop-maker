#!/usr/bin/env bash
set -euo pipefail
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
TARGET="${1:-.}"
mkdir -p "$TARGET"
install_skill_dir() {
  local destination="$1"
  mkdir -p "$TARGET/$destination"
  cp -R "$ROOT/skills/." "$TARGET/$destination/"
}
install_skill_dir ".agents/skills"
install_skill_dir ".claude/skills"
install_skill_dir ".opencode/skills"
mkdir -p "$TARGET/.opencode/agents"
cp "$ROOT/agents/loop-maker-orchestrator.md" "$TARGET/.opencode/agents/"
mkdir -p "$TARGET/.cursor/rules"
cp "$ROOT/integrations/cursor/loop-maker.mdc" "$TARGET/.cursor/rules/"
echo "Loop Maker skills installed into $TARGET"
