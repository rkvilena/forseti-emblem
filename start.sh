#!/usr/bin/env bash
# Starts frontend in a separate terminal window, then runs backend in this terminal.

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
FRONTEND_DIR="$SCRIPT_DIR/frontend"
BACKEND_DIR="$SCRIPT_DIR/backend"

start_frontend_background() {
	if [ ! -d "$FRONTEND_DIR" ]; then
		echo "[start.sh] frontend/ not found; skipping frontend start"
		return 0
	fi

	if [ ! -f "$FRONTEND_DIR/start.sh" ]; then
		echo "[start.sh] frontend/start.sh not found; skipping frontend start"
		return 0
	fi

	echo "[start.sh] Starting frontend in background in this terminal..."
	(cd "$FRONTEND_DIR" && ./start.sh) >"$SCRIPT_DIR/frontend.log" 2>&1 &
	echo "[start.sh] Frontend logs: $SCRIPT_DIR/frontend.log"
}

start_frontend_background

echo "[start.sh] Waiting 3 seconds before starting backend..."
sleep 3
echo "[start.sh] Starting backend in this terminal..."
source "$BACKEND_DIR/.venv/Scripts/activate"
exec "$BACKEND_DIR/start.sh"
