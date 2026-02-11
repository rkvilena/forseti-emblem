#!/bin/bash

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

PID_FILE="$SCRIPT_DIR/.frontend_dev.pid"

cleanup() {
	if [ -f "$PID_FILE" ]; then
		rm -f "$PID_FILE" || true
	fi
}

trap cleanup EXIT

echo "🔥 Forsetiemblem Frontend - Development Mode"
echo "============================================"

if [ ! -d "node_modules" ]; then
	echo "📦 Installing dependencies..."
	npm install
fi

if [ ! -f ".env" ]; then
	echo "⚠️  No .env file found. Copying from .env.example..."
	cp .env.example .env
fi

echo ""
echo "🚀 Starting Next.js development server with Turbopack..."
echo "   This provides Vite-like fast refresh experience."
echo ""
echo "   Frontend: http://localhost:3000"
echo "   Backend:  http://localhost:8000 (make sure it's running)"
echo ""

npm run dev &
DEV_PID=$!
echo "$DEV_PID" > "$PID_FILE"
wait "$DEV_PID"
