#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

CHECK=0
TYPECHECK=0

for arg in "$@"; do
  case "$arg" in
    --check)
      CHECK=1
      ;;
    --typecheck)
      TYPECHECK=1
      ;;
    *)
      echo "Unknown argument: $arg" >&2
      echo "Usage: frontend/format.sh [--check] [--typecheck]" >&2
      exit 2
      ;;
  esac
done

if [ ! -x "./node_modules/.bin/prettier" ]; then
  echo "[frontend] prettier skipped: local prettier is not installed" >&2
  echo "          Run: cd frontend && npm install" >&2
  exit 1
fi

PRETTIER_CMD=("./node_modules/.bin/prettier")

if [ "$CHECK" -eq 1 ]; then
  echo "[frontend] prettier (check)"
  "${PRETTIER_CMD[@]}" --check .
else
  echo "[frontend] prettier"
  "${PRETTIER_CMD[@]}" --write .
fi

if [ "$TYPECHECK" -eq 1 ]; then
  echo "[frontend] tsc typecheck"
  npm run -s type-check
fi
