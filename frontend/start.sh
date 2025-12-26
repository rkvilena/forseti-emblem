#!/bin/bash
# Local development script for Forsetiemblem Frontend
# Provides fast development experience with Turbopack

set -e

echo "🔥 Forsetiemblem Frontend - Development Mode"
echo "============================================"

# Check if node_modules exists
if [ ! -d "node_modules" ]; then
    echo "📦 Installing dependencies..."
    npm install
fi

# Check for .env file
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

npm run dev
