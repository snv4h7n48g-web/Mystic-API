# Mystic API - Windows Bedrock Verification Script
# Run with: .\verify.ps1

Write-Host "=============================================" -ForegroundColor Cyan
Write-Host "  AWS Bedrock Verification" -ForegroundColor Cyan
Write-Host "=============================================" -ForegroundColor Cyan
Write-Host ""

# Check if virtual environment exists
if (-not (Test-Path "venv")) {
    Write-Host "ERROR: Virtual environment not found. Run .\setup.ps1 first" -ForegroundColor Red
    exit 1
}

# Run verification
& .\venv\Scripts\python.exe verify_bedrock.py

exit $LASTEXITCODE
