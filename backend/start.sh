#!/usr/bin/env bash
set -euo pipefail

# Run from repo root so `backend.app.*` imports work and config can find backend/.env.
SCRIPT_DIR="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd -- "$SCRIPT_DIR/.." && pwd)"
cd "$REPO_ROOT"

exec python -m uvicorn backend.app.main:app --reload