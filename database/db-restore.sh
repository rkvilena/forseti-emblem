#!/usr/bin/env bash
# Restore a pg_dump custom archive into the LOCAL database.
#
#   bash database/db-restore.sh backups/local/forsetiemblem-local-20261104-171544.dump
#   bash database/db-restore.sh backups/prod/forsetiemblem-prod-20261104-171544.dump
#
# Restore is intentionally LOCAL-ONLY. Populating a production database is a
# deliberate Supabase operation, not a casual local script. The target database
# is dropped and recreated before the archive is loaded, so anything currently
# in the local database is replaced by the snapshot.

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"
cd "$REPO_ROOT"

DB_CONTAINER="${DB_CONTAINER:-forsetiemblem-db}"
DB_NAME="${DB_NAME:-forsetiemblem}"
DB_USER="${DB_USER:-postgres}"

ASSUME_YES=0
DUMP_FILE=""
TARGET="local"

usage() {
  cat <<'EOF'
Usage: bash database/db-restore.sh <dump-file> [local] [-y|--yes]

  <dump-file>   Path to a .dump archive created by database/db-dump.sh
  local         Restore target (only 'local' is supported)
  -y, --yes     Skip the confirmation prompt (for scripting)

Environment variables:
  DB_CONTAINER  Local container name (default: forsetiemblem-db)
  DB_USER       Local database user  (default: postgres)
  DB_NAME       Local database name  (default: forsetiemblem)
EOF
}

die() {
  echo "error: $*" >&2
  exit 1
}

for arg in "$@"; do
  case "$arg" in
    -h | --help)
      usage
      exit 0
      ;;
    -y | --yes)
      ASSUME_YES=1
      ;;
    local | prod)
      TARGET="$arg"
      ;;
    -*)
      die "unknown option '$arg'."
      ;;
    *)
      if [[ -n "$DUMP_FILE" ]]; then
        die "unexpected extra argument '$arg'."
      fi
      DUMP_FILE="$arg"
      ;;
  esac
done

[[ -n "$DUMP_FILE" ]] || {
  usage
  exit 1
}

# Resolve relative paths against the repo root (the script's working directory).
if [[ "$DUMP_FILE" != /* ]]; then
  DUMP_FILE="$REPO_ROOT/$DUMP_FILE"
fi

if [[ "$TARGET" != "local" ]]; then
  die "restore target '$TARGET' is not supported; only 'local' is allowed."
fi

[[ -f "$DUMP_FILE" ]] || die "dump file not found: $DUMP_FILE"
[[ -s "$DUMP_FILE" ]] || die "dump file is empty: $DUMP_FILE"

command -v docker >/dev/null 2>&1 || die "docker is not available on PATH."

if ! docker ps --format '{{.Names}}' | grep -q "^${DB_CONTAINER}\$"; then
  die "container '$DB_CONTAINER' is not running (start it first)."
fi

echo "[db-restore] Dump:   $DUMP_FILE"
echo "[db-restore] Target: local database '$DB_NAME' in container '$DB_CONTAINER'"
echo "[db-restore] This DROPs and recreates '$DB_NAME', then loads the snapshot."

if [[ "$ASSUME_YES" -ne 1 ]]; then
  read -r -p "Are you sure? [y/N] " REPLY
  if [[ ! "$REPLY" =~ ^[Yy]$ ]]; then
    echo "Aborted."
    exit 0
  fi
fi

echo "[db-restore] Terminating existing connections to '$DB_NAME'..."
docker exec "$DB_CONTAINER" psql -U "$DB_USER" -d postgres -c \
  "SELECT pg_terminate_backend(pid) FROM pg_stat_activity WHERE datname = '${DB_NAME}' AND pid <> pg_backend_pid();" >/dev/null 2>&1 || true

echo "[db-restore] Dropping database '$DB_NAME'..."
docker exec "$DB_CONTAINER" psql -U "$DB_USER" -d postgres -c "DROP DATABASE IF EXISTS \"${DB_NAME}\";" >/dev/null

echo "[db-restore] Recreating database '$DB_NAME'..."
docker exec "$DB_CONTAINER" psql -U "$DB_USER" -d postgres -c "CREATE DATABASE \"${DB_NAME}\";" >/dev/null

echo "[db-restore] Ensuring pgvector extension exists in '$DB_NAME'..."
docker exec "$DB_CONTAINER" psql -U "$DB_USER" -d "$DB_NAME" -c "CREATE EXTENSION IF NOT EXISTS vector;" >/dev/null 2>&1 || true

echo "[db-restore] Restoring archive..."
docker exec -i "$DB_CONTAINER" \
  pg_restore -U "$DB_USER" -d "$DB_NAME" --no-owner \
  <"$DUMP_FILE"

echo "[db-restore] Done. Database '$DB_NAME' restored from snapshot."
echo "[db-restore] Restart the backend (or run 'alembic -c backend/alembic.ini upgrade head') so migrations reconcile the schema."
