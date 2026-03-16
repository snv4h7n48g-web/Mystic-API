# Mystic API - Windows Start Script
# Run with: .\start.ps1

Write-Host "=============================================" -ForegroundColor Cyan
Write-Host "  Mystic API - Starting Server" -ForegroundColor Cyan
Write-Host "=============================================" -ForegroundColor Cyan
Write-Host ""

# Check if virtual environment exists
if (-not (Test-Path "venv")) {
    Write-Host "WARNING: Virtual environment not found. Run .\setup.ps1 first" -ForegroundColor Yellow
    exit 1
}

# Check if database is running
$dbRunning = docker ps 2>$null | Select-String "mystic_postgres"
if (-not $dbRunning) {
    Write-Host "WARNING: PostgreSQL container not running. Starting..." -ForegroundColor Yellow
    docker-compose up -d
    Start-Sleep -Seconds 3
}

Write-Host "SUCCESS: Starting FastAPI server..." -ForegroundColor Green
Write-Host ""
Write-Host "API will be available at:" -ForegroundColor Cyan
Write-Host "  - Main API: http://localhost:8000"
Write-Host "  - Documentation: http://localhost:8000/docs"
Write-Host "  - Health check: http://localhost:8000/health"
Write-Host ""
Write-Host "Press Ctrl+C to stop the server" -ForegroundColor Yellow
Write-Host ""

# Start the server
& .\venv\Scripts\uvicorn.exe main:app --reload --host 0.0.0.0 --port 8000
