#!/bin/bash
set -e

# Colors for output
GREEN='\033[0;32m'
RED='\033[0;31m'
NC='\033[0m'

echo "============================================="
echo "  AWS Bedrock Verification"
echo "============================================="
echo ""

# Check if virtual environment exists
if [ ! -d "venv" ]; then
    echo -e "${RED}✗${NC} Virtual environment not found. Run ./setup.sh first"
    exit 1
fi

# Run verification using venv python
./venv/bin/python3 verify_bedrock.py

exit $?
