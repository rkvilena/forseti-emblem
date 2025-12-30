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
      echo "Usage: backend/format.sh [--check] [--typecheck]" >&2
      exit 2
      ;;
  esac
done

PYTHON_BIN="${PYTHON_BIN:-}"

# Prefer project venv if present (works even if not activated)
if [ -n "$PYTHON_BIN" ]; then
  :
elif [ -x "./.venv/Scripts/python.exe" ]; then
  PYTHON_BIN="./.venv/Scripts/python.exe"
elif [ -x "./.venv/bin/python" ]; then
  PYTHON_BIN="./.venv/bin/python"
elif command -v python >/dev/null 2>&1; then
  PYTHON_BIN="python"
elif command -v python3 >/dev/null 2>&1; then
  PYTHON_BIN="python3"
else
  echo "Python not found on PATH and backend/.venv not found." >&2
  exit 1
fi

if ! "$PYTHON_BIN" -m ruff --version >/dev/null 2>&1; then
  echo "ruff is not installed in this Python environment." >&2
  echo "Install with: $PYTHON_BIN -m pip install -r requirements.txt" >&2
  exit 1
fi

if [ "$CHECK" -eq 1 ]; then
  echo "[backend] ruff format (check)"
  "$PYTHON_BIN" -m ruff format --check .
else
  echo "[backend] ruff format"
  "$PYTHON_BIN" -m ruff format .
fi

if [ "$TYPECHECK" -eq 1 ]; then
  if ! "$PYTHON_BIN" -m mypy --version >/dev/null 2>&1; then
    echo "mypy is not installed in this Python environment." >&2
    echo "Install with: $PYTHON_BIN -m pip install -r requirements.txt" >&2
    exit 1
  fi

  echo "[backend] mypy typecheck"
  "$PYTHON_BIN" -m mypy app
fi
