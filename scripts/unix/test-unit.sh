#!/bin/bash
set -e

echo "============================================="
echo "  Mystic API - Running Unit Tests (pytest)"
echo "============================================="
echo ""

if [ ! -d "venv" ]; then
    echo "ERROR: Virtual environment not found. Run ./setup.sh first"
    exit 1
fi

./venv/bin/python3 -m pytest -q
