#!/usr/bin/env bash
# Snapshot the Forsetiemblem database into backups/<mode>/ as a pg_dump custom
# archive. One interface for both environments:
#
#   bash database/db-dump.sh local   # dump the local Docker Postgres container
#   bash database/db-dump.sh prod    # dump the production database (DATABASE_URL)
#
# Local and prod differ only in *how* pg_dump is invoked, never in the command
# the operator types or in the output format. Dumps are never uploaded.

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"
cd "$REPO_ROOT"

BACKEND_ENV="$REPO_ROOT/backend/.env"
PROD_ENV="$REPO_ROOT/database/.env.prod"

# Local database (kept consistent with db-reset.sh).
DB_CONTAINER="${DB_CONTAINER:-forsetiemblem-db}"
DB_USER="${DB_USER:-postgres}"
DB_NAME="${DB_NAME:-forsetiemblem}"

# Temporary client image used for prod dumps.
PG_CLIENT_IMAGE="${PG_CLIENT_IMAGE:-postgres:17-alpine}"

usage() {
  cat <<'EOF'
Usage: bash database/db-dump.sh <local|prod>

  local   Dump the local Docker database (container: forsetiemblem-db)
  prod    Dump the production database via DATABASE_URL

Environment variables:
  DATABASE_URL     Required for prod (or set it in backend/.env.prod)
  DB_CONTAINER     Local container name   (default: forsetiemblem-db)
  DB_USER          Local database user    (default: postgres)
  DB_NAME          Local database name    (default: forsetiemblem)
  PG_CLIENT_IMAGE  Client image for prod  (default: postgres:16-alpine)

Output:
  backups/local/forsetiemblem-local-YYYYMMDD-HHMMSS.dump
  backups/prod/forsetiemblem-prod-YYYYMMDD-HHMMSS.dump
EOF
}

die() {
  echo "error: $*" >&2
  exit 1
}

# postgresql+psycopg:// -> postgresql:// (client tools reject the SQLAlchemy scheme).
normalize_url() {
  local url="$1"
  url="${url/postgresql+psycopg:\/\//postgresql:\/\/}"
  url="${url/postgresql+asyncpg:\/\//postgresql:\/\/}"
  printf '%s' "$url"
}

require_docker() {
  command -v docker >/dev/null 2>&1 || die "docker is not available on PATH."
}

if [[ $# -ne 1 ]]; then
  usage
  exit 1
fi

MODE="$1"
case "$MODE" in
  local | prod) ;;
  -h | --help)
    usage
    exit 0
    ;;
  *)
    die "unknown mode '$MODE' (expected 'local' or 'prod')."
    ;;
esac

require_docker

OUT_DIR="$REPO_ROOT/backups/$MODE"
mkdir -p "$OUT_DIR"

STAMP="$(date +%Y%m%d-%H%M%S)"
OUT_FILE="$OUT_DIR/forsetiemblem-$MODE-$STAMP.dump"

if [[ -e "$OUT_FILE" ]]; then
  die "refusing to overwrite existing file: $OUT_FILE"
fi

echo "[db-dump] Mode:   $MODE"
echo "[db-dump] Output: $OUT_FILE"

if [[ "$MODE" == "local" ]]; then
  if ! docker ps --format '{{.Names}}' | grep -q "^${DB_CONTAINER}\$"; then
    die "container '$DB_CONTAINER' is not running (start it, or use 'bash database/db-dump.sh prod')."
  fi

  echo "[db-dump] Dumping local database '$DB_NAME' from container '$DB_CONTAINER'..."

  docker exec "$DB_CONTAINER" \
    pg_dump \
    -U "$DB_USER" \
    -d "$DB_NAME" \
    --format=custom \
    --no-owner \
    >"$OUT_FILE"

else
  # Load prod DATABASE_URL from backend/.env.prod unless already provided.
  if [[ -z "${DATABASE_URL:-}" && -f "$PROD_ENV" ]]; then
    # shellcheck disable=SC1090
    set -a
    source "$PROD_ENV"
    set +a
  fi

  [[ -n "${DATABASE_URL:-}" ]] || die "DATABASE_URL is not set (set it or create backend/.env.prod)."

  DB_URL="$(normalize_url "$DATABASE_URL")"
  # Never echo DB_URL: it may contain credentials.

  echo "[db-dump] Dumping production database via '$PG_CLIENT_IMAGE'..."

  docker run --rm \
    -e "DUMP_URL=$DB_URL" \
    "$PG_CLIENT_IMAGE" \
    sh -c 'pg_dump --dbname="$DUMP_URL" --format=custom --no-owner' \
    >"$OUT_FILE"
fi

if [[ ! -s "$OUT_FILE" ]]; then
  rm -f "$OUT_FILE"
  die "dump produced no output; nothing was written."
fi

SIZE="$(du -h "$OUT_FILE" | cut -f1)"
echo "[db-dump] Done."
echo "[db-dump] File: $OUT_FILE ($SIZE)"
echo "[db-dump] Inspect: pg_restore --list \"$OUT_FILE\""
