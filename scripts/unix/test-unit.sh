#!/bin/bash
set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "${SCRIPT_DIR}/../.." && pwd)"
BACKEND_DIR="${REPO_ROOT}/backend"

cd "${BACKEND_DIR}"

echo "============================================="
echo "  Mystic API - Running Unit Tests (pytest)"
echo "============================================="
echo ""

if [ ! -d "venv" ]; then
    echo "ERROR: Virtual environment not found at ${BACKEND_DIR}/venv. Run ./scripts/unix/setup.sh first"
    exit 1
fi

./venv/bin/python3 -m pytest -q
