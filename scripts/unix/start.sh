#!/bin/bash
set -e

# Colors for output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo "============================================="
echo "  Mystic API - Starting Server"
echo "============================================="
echo ""

# Check if virtual environment exists
if [ ! -d "venv" ]; then
    echo -e "${YELLOW}⚠${NC} Virtual environment not found. Run ./setup.sh first"
    exit 1
fi

# Activate virtual environment
source venv/bin/activate

# Check if database is running
if ! docker ps | grep -q mystic_postgres; then
    echo -e "${YELLOW}⚠${NC} PostgreSQL container not running. Starting..."
    docker-compose up -d
    sleep 3
fi

# Load environment variables
set -a
source .env
set +a

# Start the server
echo -e "${GREEN}✓${NC} Starting FastAPI server..."
echo ""
echo "API will be available at:"
echo "  - Main API: http://localhost:8000"
echo "  - Documentation: http://localhost:8000/docs"
echo "  - Health check: http://localhost:8000/health"
echo ""
echo "Press Ctrl+C to stop the server"
echo ""

uvicorn main:app --reload --host 0.0.0.0 --port 8000
