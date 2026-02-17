#!/usr/bin/env bash
set -euo pipefail

cd "$(dirname "$0")"

echo "[alembic] Running database migrations..."
if ! alembic -c alembic.ini upgrade head; then
  echo "Database migration failed; aborting startup." >&2
  exit 1
fi

echo "[app] Starting application server..."
exec python -m uvicorn app.main:app --host "${HOST:-0.0.0.0}" --port "${PORT:-8080}"
