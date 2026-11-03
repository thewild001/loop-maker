#!/usr/bin/env bash
# Instala las skills de Loop Maker sin apropiarse de la configuración del proyecto.
set -euo pipefail
REPO="thewild001/loop-maker"
BRANCH="${LOOP_MAKER_BRANCH:-main}"
command -v curl >/dev/null || { echo "curl es necesario" >&2; exit 1; }
command -v tar >/dev/null || { echo "tar es necesario" >&2; exit 1; }
TMP="$(mktemp -d)"
trap 'rm -rf "$TMP"' EXIT
curl -fsSL --retry 3 "https://codeload.github.com/$REPO/tar.gz/refs/heads/$BRANCH" -o "$TMP/repo.tgz"
tar -xzf "$TMP/repo.tgz" -C "$TMP"
ROOT="$(find "$TMP" -mindepth 1 -maxdepth 1 -type d | head -1)"
[[ -f "$ROOT/scripts/install-skills.sh" ]] || { echo "Archivo Loop Maker inválido" >&2; exit 1; }
bash "$ROOT/scripts/install-skills.sh" "$(pwd)"
echo "Siguiente paso: instala el extra MCP y registra loop-maker-mcp en tu agente."
