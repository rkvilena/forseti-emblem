#!/usr/bin/env bash
set -euo pipefail

cd "$(dirname "$0")"

if [ -f ".env" ]; then
  set -a
  source .env
  set +a
fi

if [ -f ".venv/Scripts/activate" ]; then
  source .venv/Scripts/activate
else
  echo ".venv not found. run: python -m venv .venv" >&2
  exit 1
fi

exec python -m fastapi dev app/main.py