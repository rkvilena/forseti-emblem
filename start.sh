#!/usr/bin/env bash
# Starts frontend in a separate terminal window, then runs backend in this terminal.

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
FRONTEND_DIR="$SCRIPT_DIR/frontend"
BACKEND_DIR="$SCRIPT_DIR/backend"
FRONTEND_PID_FILE="$FRONTEND_DIR/.frontend_dev.pid"

echo "[start.sh] Starting frontend in separate shell..."
if [ -x "/git-bash.exe" ]; then
	/git-bash.exe -c "cd '$FRONTEND_DIR' && bash start.sh" &
else
	(cd "$FRONTEND_DIR" && bash start.sh) &
fi
FRONTEND_SHELL_PID=$!

cleanup() {
	if [ -f "$FRONTEND_PID_FILE" ]; then
		FRONTEND_PID="$(cat "$FRONTEND_PID_FILE" 2>/dev/null || true)"
		if [ -n "$FRONTEND_PID" ] && kill -0 "$FRONTEND_PID" 2>/dev/null; then
			kill "$FRONTEND_PID" >/dev/null 2>&1 || true
		fi
	fi
	if command -v netstat >/dev/null 2>&1 && command -v taskkill >/dev/null 2>&1; then
		PORT_PID="$(netstat -ano | grep ":3000" | awk '{print $NF}' | head -n 1 || true)"
		if [ -n "$PORT_PID" ]; then
			taskkill //F //PID "$PORT_PID" >/dev/null 2>&1 || true
		fi
	fi
	if kill -0 "$FRONTEND_SHELL_PID" 2>/dev/null; then
		kill "$FRONTEND_SHELL_PID" >/dev/null 2>&1 || true
	fi
}
trap cleanup EXIT

echo "[start.sh] Waiting 3 seconds before starting backend..."
sleep 3

echo "[start.sh] Starting backend..."
bash "$BACKEND_DIR/start.sh"
