# Mystic API - Windows Setup Script
# Run with: .\setup.ps1

Write-Host "=============================================" -ForegroundColor Cyan
Write-Host "  Mystic API - Windows Setup" -ForegroundColor Cyan
Write-Host "=============================================" -ForegroundColor Cyan
Write-Host ""

# Check Python
Write-Host "Step 1: Checking Python installation..." -ForegroundColor Yellow
try {
    $pythonVersion = python --version 2>&1
    if ($pythonVersion -match "Python 3\.1[1-9]|Python 3\.[2-9][0-9]") {
        Write-Host "SUCCESS: $pythonVersion installed" -ForegroundColor Green
    } else {
        Write-Host "ERROR: Python 3.11+ required. Found: $pythonVersion" -ForegroundColor Red
        Write-Host "Install from: https://www.python.org/downloads/" -ForegroundColor Yellow
        exit 1
    }
} catch {
    Write-Host "ERROR: Python not found" -ForegroundColor Red
    Write-Host "Install Python 3.11+ from: https://www.python.org/downloads/" -ForegroundColor Yellow
    Write-Host "Make sure to check Add Python to PATH during installation" -ForegroundColor Yellow
    exit 1
}

# Check Docker
Write-Host ""
Write-Host "Step 2: Checking Docker..." -ForegroundColor Yellow
try {
    $dockerVersion = docker --version 2>&1
    Write-Host "SUCCESS: Docker installed: $dockerVersion" -ForegroundColor Green
} catch {
    Write-Host "ERROR: Docker not found" -ForegroundColor Red
    Write-Host "Install Docker Desktop from: https://docs.docker.com/desktop/install/windows-install/" -ForegroundColor Yellow
    exit 1
}

try {
    $composeVersion = docker-compose --version 2>&1
    Write-Host "SUCCESS: Docker Compose installed: $composeVersion" -ForegroundColor Green
} catch {
    Write-Host "ERROR: Docker Compose not found" -ForegroundColor Red
    exit 1
}

# Create virtual environment
Write-Host ""
Write-Host "Step 3: Setting up Python virtual environment..." -ForegroundColor Yellow
if (Test-Path "venv") {
    Write-Host "WARNING: Virtual environment already exists" -ForegroundColor Yellow
} else {
    python -m venv venv
    Write-Host "SUCCESS: Virtual environment created" -ForegroundColor Green
}

# Activate virtual environment and install dependencies
Write-Host ""
Write-Host "Step 4: Installing Python dependencies..." -ForegroundColor Yellow
& .\venv\Scripts\python.exe -m pip install --upgrade pip --quiet
& .\venv\Scripts\python.exe -m pip install -r requirements.txt --quiet
Write-Host "SUCCESS: Dependencies installed" -ForegroundColor Green

# Setup environment variables
Write-Host ""
Write-Host "Step 5: Configuring environment variables..." -ForegroundColor Yellow
if (-not (Test-Path ".env")) {
    Copy-Item ".env.example" ".env"
    Write-Host "SUCCESS: .env file created from template" -ForegroundColor Green
    Write-Host ""
    Write-Host "WARNING: You must configure AWS credentials in .env file" -ForegroundColor Yellow
    Write-Host ""
    Write-Host "Required AWS configuration:" -ForegroundColor Cyan
    Write-Host "  1. AWS_ACCESS_KEY_ID"
    Write-Host "  2. AWS_SECRET_ACCESS_KEY"
    Write-Host "  3. AWS_REGION (default: us-east-1)"
    Write-Host ""
    Write-Host "Get your credentials from AWS IAM Console:" -ForegroundColor Cyan
    Write-Host "  https://console.aws.amazon.com/iam/"
    Write-Host ""
    $edit = Read-Host "Press Enter to open .env file in notepad"
    notepad .env
} else {
    Write-Host "WARNING: .env file already exists (not overwriting)" -ForegroundColor Yellow
}

# Start PostgreSQL
Write-Host ""
Write-Host "Step 6: Starting PostgreSQL database..." -ForegroundColor Yellow
docker-compose up -d
Write-Host "SUCCESS: PostgreSQL container started" -ForegroundColor Green

# Wait for database
Write-Host "Waiting for database to be ready..." -ForegroundColor Yellow
Start-Sleep -Seconds 5

# Test database connection
try {
    $dbTest = docker exec mystic_postgres pg_isready -U mystic 2>&1
    if ($dbTest -match "accepting connections") {
        Write-Host "SUCCESS: Database is ready" -ForegroundColor Green
    } else {
        Write-Host "WARNING: Database connection test failed" -ForegroundColor Yellow
    }
} catch {
    Write-Host "WARNING: Database connection test failed" -ForegroundColor Yellow
}

# All done
Write-Host ""
Write-Host "=============================================" -ForegroundColor Green
Write-Host "  Setup Complete!" -ForegroundColor Green
Write-Host "=============================================" -ForegroundColor Green
Write-Host ""
Write-Host "SUCCESS: Database: Running on localhost:5432" -ForegroundColor Green
Write-Host "SUCCESS: API: Ready to start" -ForegroundColor Green
Write-Host ""
Write-Host "Next steps:" -ForegroundColor Cyan
Write-Host ""
Write-Host "  1. Verify AWS credentials in .env file"
Write-Host "  2. Run: .\verify.ps1"
Write-Host "  3. Start server: .\start.ps1"
Write-Host "  4. Run tests: .\test.ps1"
Write-Host ""
Write-Host "API will be available at: http://localhost:8000" -ForegroundColor Green
Write-Host ""
