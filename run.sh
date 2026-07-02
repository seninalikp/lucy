#!/usr/bin/env bash
# LUCY Part 0 — Spine Server Launcher

echo ""
echo "  ╔══════════════════════════════════╗"
echo "  ║   LUCY — Spine Config Server     ║"
echo "  ║   Part 0 of 10                   ║"
echo "  ╚══════════════════════════════════╝"
echo ""

# Check Python
if ! command -v python3 &>/dev/null; then
  echo "  ✗ Python 3 not found. Please install it first."
  exit 1
fi

# Install deps if needed
if ! python3 -c "import flask" 2>/dev/null; then
  echo "  → Installing dependencies..."
  pip3 install -r requirements.txt --quiet
fi

echo "  → Starting server at http://localhost:7700"
echo "  → Open your browser to http://localhost:7700"
echo "  → Edit data/spine.json — changes are live on refresh"
echo "  → Press Ctrl+C to stop"
echo ""

cd "$(dirname "$0")"
python3 backend/server.py
