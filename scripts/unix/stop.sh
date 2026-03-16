#!/bin/bash

# Colors for output
GREEN='\033[0;32m'
NC='\033[0m' # No Color

echo "============================================="
echo "  Mystic API - Cleanup"
echo "============================================="
echo ""

# Stop Docker containers
if docker ps | grep -q mystic_postgres; then
    echo "Stopping PostgreSQL container..."
    docker-compose down
    echo -e "${GREEN}✓${NC} Containers stopped"
else
    echo "No containers running"
fi

echo ""
echo "Cleanup options:"
echo ""
echo "  1. Stop containers only (done above)"
echo "  2. Remove database data: docker-compose down -v"
echo "  3. Remove virtual environment: rm -rf venv"
echo ""
