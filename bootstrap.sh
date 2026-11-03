#!/usr/bin/env bash
# Instala skills de Loop Maker sin apropiarse de la configuración del proyecto.
set -euo pipefail
REPO="thewild001/loop-maker"
BRANCH="${LOOP_MAKER_BRANCH:-main}"
TARGET="."
FORCE=()
while [[ $# -gt 0 ]]; do
  case "$1" in
    --target|-t) [[ $# -ge 2 ]] || { echo "--target requiere una ruta" >&2; exit 2; }; TARGET="$2"; shift 2 ;;
    --force|-f) FORCE=(--force); shift ;;
    -h|--help) echo "Usage: bootstrap.sh [--target DIR] [--force]"; exit 0 ;;
    *) echo "Opción desconocida: $1" >&2; exit 2 ;;
  esac
done
command -v curl >/dev/null || { echo "curl es necesario" >&2; exit 1; }
command -v tar >/dev/null || { echo "tar es necesario" >&2; exit 1; }
TMP="$(mktemp -d)"
trap 'rm -rf "$TMP"' EXIT
curl -fsSL --retry 3 "https://codeload.github.com/$REPO/tar.gz/refs/heads/$BRANCH" -o "$TMP/repo.tgz"
tar -xzf "$TMP/repo.tgz" -C "$TMP"
ROOT="$(find "$TMP" -mindepth 1 -maxdepth 1 -type d | head -1)"
[[ -f "$ROOT/scripts/install-skills.sh" ]] || { echo "Archivo Loop Maker inválido" >&2; exit 1; }
bash "$ROOT/scripts/install-skills.sh" --target "$TARGET" "${FORCE[@]}"
echo "Siguiente paso: abre el proyecto en tu agente e invoca /loop-maker."
