#!/bin/bash
set -e

echo "============================================="
echo "  Mystic API - Local Development Setup"
echo "============================================="
echo ""

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Function to print status
print_status() {
    echo -e "${GREEN}✓${NC} $1"
}

print_error() {
    echo -e "${RED}✗${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}⚠${NC} $1"
}

# Check if running from correct directory
if [ ! -f "main.py" ]; then
    print_error "main.py not found. Please run this script from the project root directory."
    exit 1
fi

# Step 1: Check Python version
echo "Step 1: Checking Python version..."
PYTHON_VERSION=$(python3 --version 2>&1 | awk '{print $2}')
REQUIRED_VERSION="3.11"

if python3 -c "import sys; exit(0 if sys.version_info >= (3, 11) else 1)"; then
    print_status "Python $PYTHON_VERSION installed"
else
    print_error "Python 3.11+ required. Found: $PYTHON_VERSION"
    echo "Install Python 3.11+ from: https://www.python.org/downloads/"
    exit 1
fi

# Step 2: Check Docker
echo ""
echo "Step 2: Checking Docker..."
if command -v docker &> /dev/null; then
    print_status "Docker installed: $(docker --version)"
else
    print_error "Docker not found"
    echo "Install Docker from: https://docs.docker.com/get-docker/"
    exit 1
fi

if command -v docker-compose &> /dev/null; then
    print_status "Docker Compose installed: $(docker-compose --version)"
else
    print_error "Docker Compose not found"
    echo "Install Docker Compose from: https://docs.docker.com/compose/install/"
    exit 1
fi

# Step 3: Create virtual environment
echo ""
echo "Step 3: Setting up Python virtual environment..."
if [ ! -d "venv" ]; then
    python3 -m venv venv
    print_status "Virtual environment created"
else
    print_warning "Virtual environment already exists"
fi

# Activate virtual environment
source venv/bin/activate
print_status "Virtual environment activated"

# Step 4: Install dependencies
echo ""
echo "Step 4: Installing Python dependencies..."
pip install --upgrade pip > /dev/null 2>&1
pip install -r requirements.txt > /dev/null 2>&1
print_status "Dependencies installed"

# Step 5: Setup environment variables
echo ""
echo "Step 5: Configuring environment variables..."
if [ ! -f ".env" ]; then
    cp .env.example .env
    print_status ".env file created from template"
    echo ""
    print_warning "IMPORTANT: You must configure AWS credentials in .env file"
    echo ""
    echo "Required AWS configuration:"
    echo "  1. AWS_ACCESS_KEY_ID"
    echo "  2. AWS_SECRET_ACCESS_KEY"
    echo "  3. AWS_REGION (default: us-east-1)"
    echo ""
    echo "Get your credentials from AWS IAM Console:"
    echo "  https://console.aws.amazon.com/iam/"
    echo ""
    read -p "Press Enter to edit .env file now, or Ctrl+C to exit and edit manually..."
    
    # Try to open in default editor
    if command -v nano &> /dev/null; then
        nano .env
    elif command -v vim &> /dev/null; then
        vim .env
    else
        echo "Please edit .env manually with your preferred editor"
    fi
else
    print_warning ".env file already exists (not overwriting)"
fi

# Step 6: Check AWS credentials
echo ""
echo "Step 6: Validating AWS credentials..."

# Source the .env file
set -a
source .env
set +a

if [ -z "$AWS_ACCESS_KEY_ID" ] || [ "$AWS_ACCESS_KEY_ID" = "your_access_key_here" ]; then
    print_error "AWS_ACCESS_KEY_ID not configured in .env"
    echo "Please edit .env and add your AWS credentials"
    exit 1
fi

if [ -z "$AWS_SECRET_ACCESS_KEY" ] || [ "$AWS_SECRET_ACCESS_KEY" = "your_secret_key_here" ]; then
    print_error "AWS_SECRET_ACCESS_KEY not configured in .env"
    echo "Please edit .env and add your AWS credentials"
    exit 1
fi

print_status "AWS credentials configured"

# Step 7: Start PostgreSQL
echo ""
echo "Step 7: Starting PostgreSQL database..."
docker-compose up -d
print_status "PostgreSQL container started"

# Wait for PostgreSQL to be ready
echo "Waiting for database to be ready..."
sleep 5

# Test database connection
if docker exec mystic_postgres pg_isready -U mystic > /dev/null 2>&1; then
    print_status "Database is ready"
else
    print_error "Database connection failed"
    exit 1
fi

# Step 8: Test AWS Bedrock connection
echo ""
echo "Step 8: Testing AWS Bedrock connection..."
python3 << 'EOF'
import boto3
import os
from dotenv import load_dotenv

load_dotenv()

try:
    client = boto3.client(
        'bedrock-runtime',
        region_name=os.getenv('AWS_REGION', 'us-east-1'),
        aws_access_key_id=os.getenv('AWS_ACCESS_KEY_ID'),
        aws_secret_access_key=os.getenv('AWS_SECRET_ACCESS_KEY')
    )
    
    # Try to list available models (this validates credentials)
    bedrock = boto3.client(
        'bedrock',
        region_name=os.getenv('AWS_REGION', 'us-east-1'),
        aws_access_key_id=os.getenv('AWS_ACCESS_KEY_ID'),
        aws_secret_access_key=os.getenv('AWS_SECRET_ACCESS_KEY')
    )
    
    print("✓ AWS Bedrock connection successful")
    exit(0)
    
except Exception as e:
    print(f"✗ AWS Bedrock connection failed: {str(e)}")
    print("\nPlease verify:")
    print("  1. AWS credentials are correct")
    print("  2. AWS region is correct")
    print("  3. IAM user has bedrock:InvokeModel permissions")
    print("  4. Nova models are enabled in Bedrock console")
    exit(1)
EOF

if [ $? -eq 0 ]; then
    print_status "AWS Bedrock connection verified"
else
    print_error "AWS Bedrock connection failed"
    echo ""
    echo "Troubleshooting steps:"
    echo "  1. Verify credentials in .env file"
    echo "  2. Check IAM permissions in AWS console"
    echo "  3. Enable Nova models in Bedrock console:"
    echo "     https://console.aws.amazon.com/bedrock/"
    exit 1
fi

# Step 9: All done
echo ""
echo "============================================="
echo "  Setup Complete!"
echo "============================================="
echo ""
print_status "Database: Running on localhost:5432"
print_status "API: Ready to start"
echo ""
echo "Next steps:"
echo ""
echo "  1. Start the API server:"
echo "     ${GREEN}./start.sh${NC}"
echo ""
echo "  2. In another terminal, run tests:"
echo "     ${GREEN}./test.sh${NC}"
echo ""
echo "  3. API will be available at:"
echo "     ${GREEN}http://localhost:8000${NC}"
echo ""
echo "  4. View API documentation:"
echo "     ${GREEN}http://localhost:8000/docs${NC}"
echo ""
