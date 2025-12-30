#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

echo "Running formatters..."

bash "$ROOT_DIR/backend/format.sh" "$@"
printf "\n"
bash "$ROOT_DIR/frontend/format.sh" "$@"

echo "Done."
