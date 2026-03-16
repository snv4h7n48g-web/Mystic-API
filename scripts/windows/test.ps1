# Mystic API - Windows Test Script
# Run with: .\test.ps1

Write-Host "=============================================" -ForegroundColor Cyan
Write-Host "  Mystic API - Running Integration Tests" -ForegroundColor Cyan
Write-Host "=============================================" -ForegroundColor Cyan
Write-Host ""

# Check if virtual environment exists
if (-not (Test-Path "venv")) {
    Write-Host "ERROR: Virtual environment not found. Run .\setup.ps1 first" -ForegroundColor Red
    exit 1
}

# Check if server is running
try {
    $response = Invoke-WebRequest -Uri "http://localhost:8000/health" -UseBasicParsing -TimeoutSec 2 -ErrorAction Stop
    Write-Host "SUCCESS: API server is running" -ForegroundColor Green
    Write-Host ""
} catch {
    Write-Host "ERROR: API server is not running" -ForegroundColor Red
    Write-Host ""
    Write-Host "Please start the server in another PowerShell window:" -ForegroundColor Yellow
    Write-Host "  .\start.ps1" -ForegroundColor Green
    Write-Host ""
    exit 1
}

# Run the test script
& .\venv\Scripts\python.exe test_api.py

if ($LASTEXITCODE -eq 0) {
    Write-Host ""
    Write-Host "=============================================" -ForegroundColor Green
    Write-Host "  SUCCESS: All Tests Passed" -ForegroundColor Green
    Write-Host "=============================================" -ForegroundColor Green
} else {
    Write-Host ""
    Write-Host "=============================================" -ForegroundColor Red
    Write-Host "  ERROR: Tests Failed" -ForegroundColor Red
    Write-Host "=============================================" -ForegroundColor Red
    exit 1
}
