# Mystic API - Windows Stop Script
# Run with: .\stop.ps1

Write-Host "=============================================" -ForegroundColor Cyan
Write-Host "  Mystic API - Cleanup" -ForegroundColor Cyan
Write-Host "=============================================" -ForegroundColor Cyan
Write-Host ""

# Stop Docker containers
$running = docker ps 2>$null | Select-String "mystic_postgres"
if ($running) {
    Write-Host "Stopping PostgreSQL container..." -ForegroundColor Yellow
    docker-compose down
    Write-Host "SUCCESS: Containers stopped" -ForegroundColor Green
} else {
    Write-Host "No containers running" -ForegroundColor Yellow
}

Write-Host ""
Write-Host "Cleanup options:" -ForegroundColor Cyan
Write-Host ""
Write-Host "  1. Stop containers only (done above)"
Write-Host "  2. Remove database data: docker-compose down -v"
Write-Host "  3. Remove virtual environment: Remove-Item -Recurse -Force venv"
Write-Host ""
