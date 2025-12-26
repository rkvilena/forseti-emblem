#!/usr/bin/env bash
# Starts frontend in a separate terminal window, then runs backend in this terminal.

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
FRONTEND_DIR="$SCRIPT_DIR/frontend"
BACKEND_DIR="$SCRIPT_DIR/backend"

start_frontend_window() {
	if [ ! -d "$FRONTEND_DIR" ]; then
		echo "[start.sh] frontend/ not found; skipping frontend start"
		return 0
	fi

	if [ ! -f "$FRONTEND_DIR/start.sh" ]; then
		echo "[start.sh] frontend/start.sh not found; skipping frontend start"
		return 0
	fi

	echo "[start.sh] Starting frontend in a separate terminal window..."

	# Preferred on Windows: spawn a new PowerShell window (most reliable from VS Code/Git Bash).
	if command -v powershell.exe >/dev/null 2>&1; then
		local win_frontend_dir
		if command -v cygpath >/dev/null 2>&1; then
			win_frontend_dir="$(cygpath -w "$FRONTEND_DIR")"
		else
			win_frontend_dir="$FRONTEND_DIR"
		fi

		# Start Next.js dev server directly (no dependency on bash in the new window).
		powershell.exe -NoProfile -Command "Start-Process -FilePath powershell.exe -WorkingDirectory '$win_frontend_dir' -ArgumentList '-NoExit','-Command','npm run dev'" >/dev/null 2>&1 || true
		return 0
	fi

	# Windows: Git Bash typically provides cmd.exe + cygpath.
	if command -v cmd.exe >/dev/null 2>&1; then
		local win_frontend_dir
		if command -v cygpath >/dev/null 2>&1; then
			win_frontend_dir="$(cygpath -w "$FRONTEND_DIR")"
		else
			# Best-effort: cmd.exe can usually handle forward slashes too.
			win_frontend_dir="$FRONTEND_DIR"
		fi

		# Open a new window titled "forsetiemblem-frontend" and run frontend/start.sh.
		# Using bash -lc ensures it runs in a login shell with PATH.
		cmd.exe /c start "forsetiemblem-frontend" /D "$win_frontend_dir" bash -lc "./start.sh"
		return 0
	fi

	# Non-Windows fallback: run in background but redirect output so logs don't mix.
	(cd "$FRONTEND_DIR" && ./start.sh) >"$SCRIPT_DIR/frontend.log" 2>&1 &
	echo "[start.sh] Frontend logs: $SCRIPT_DIR/frontend.log"
}

start_frontend_window

echo "[start.sh] Starting backend in this terminal..."
source "$BACKEND_DIR/.venv/Scripts/activate"
exec "$BACKEND_DIR/start.sh"
