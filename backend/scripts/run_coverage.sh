#!/usr/bin/env bash
set -euo pipefail

./venv/bin/pytest --cov=. --cov-report=term-missing --cov-report=xml "$@"

echo
echo "Coverage artifact: coverage.xml"
