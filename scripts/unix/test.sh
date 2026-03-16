#!/bin/bash
set -e

# Colors for output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

echo "============================================="
echo "  Mystic API - Running Integration Tests"
echo "============================================="
echo ""

# Check if virtual environment exists
if [ ! -d "venv" ]; then
    echo -e "${RED}✗${NC} Virtual environment not found. Run ./setup.sh first"
    exit 1
fi

# Check if server is running
if ! curl -s http://localhost:8000/health > /dev/null 2>&1; then
    echo -e "${RED}✗${NC} API server is not running"
    echo ""
    echo "Please start the server in another terminal:"
    echo "  ${GREEN}./start.sh${NC}"
    echo ""
    exit 1
fi

echo -e "${GREEN}✓${NC} API server is running"
echo ""

# Run the test script using venv python directly
./venv/bin/python3 test_api.py

EXIT_CODE=$?

echo ""
if [ $EXIT_CODE -eq 0 ]; then
    echo "============================================="
    echo -e "  ${GREEN}✓ All Tests Passed${NC}"
    echo "============================================="
else
    echo "============================================="
    echo -e "  ${RED}✗ Tests Failed${NC}"
    echo "============================================="
fi

exit $EXIT_CODE
