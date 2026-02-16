#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

DB_CONTAINER="${DB_CONTAINER:-forsetiemblem-db}"
DB_NAME="${DB_NAME:-forsetiemblem}"
DB_USER="${DB_USER:-postgres}"

echo "This will DROP and recreate database '$DB_NAME' in container '$DB_CONTAINER'."
read -r -p "Are you sure? [y/N] " REPLY

if [[ ! "$REPLY" =~ ^[Yy]$ ]]; then
  echo "Aborted."
  exit 0
fi

if ! command -v docker >/dev/null 2>&1; then
  echo "docker is not available on PATH." >&2
  exit 1
fi

if ! docker ps --format '{{.Names}}' | grep -q "^${DB_CONTAINER}\$"; then
  echo "Container '${DB_CONTAINER}' is not running." >&2
  exit 1
fi

echo "Terminating existing connections to '${DB_NAME}'..."
docker exec "${DB_CONTAINER}" psql -U "${DB_USER}" -d postgres -c \
  "SELECT pg_terminate_backend(pid) FROM pg_stat_activity WHERE datname = '${DB_NAME}' AND pid <> pg_backend_pid();" >/dev/null 2>&1 || true

echo "Dropping database '${DB_NAME}'..."
docker exec "${DB_CONTAINER}" psql -U "${DB_USER}" -d postgres -c "DROP DATABASE IF EXISTS \"${DB_NAME}\";"

echo "Recreating database '${DB_NAME}'..."
docker exec "${DB_CONTAINER}" psql -U "${DB_USER}" -d postgres -c "CREATE DATABASE \"${DB_NAME}\";"

echo "Ensuring pgvector extension exists in '${DB_NAME}'..."
docker exec "${DB_CONTAINER}" psql -U "${DB_USER}" -d "${DB_NAME}" -c "CREATE EXTENSION IF NOT EXISTS vector;" >/dev/null 2>&1 || true

echo "Database '${DB_NAME}' has been reset."
echo "Restart the backend so it can recreate tables via init_db()."

