# Mystic API - Windows Unit Test Script
# Run with: .\test-unit.ps1 from backend directory

Write-Host "=============================================" -ForegroundColor Cyan
Write-Host "  Mystic API - Running Unit Tests (pytest)" -ForegroundColor Cyan
Write-Host "=============================================" -ForegroundColor Cyan
Write-Host ""

if (-not (Test-Path "venv")) {
    Write-Host "ERROR: Virtual environment not found. Run .\setup.ps1 first" -ForegroundColor Red
    exit 1
}

& .\venv\Scripts\python.exe -m pytest -q

if ($LASTEXITCODE -eq 0) {
    Write-Host ""
    Write-Host "=============================================" -ForegroundColor Green
    Write-Host "  SUCCESS: Unit Tests Passed" -ForegroundColor Green
    Write-Host "=============================================" -ForegroundColor Green
} else {
    Write-Host ""
    Write-Host "=============================================" -ForegroundColor Red
    Write-Host "  ERROR: Unit Tests Failed" -ForegroundColor Red
    Write-Host "=============================================" -ForegroundColor Red
    exit 1
}
