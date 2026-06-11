# Start the Payroll app with Docker Compose
$ErrorActionPreference = "Stop"
Set-Location $PSScriptRoot

Write-Host "Starting Payroll application (Docker)..." -ForegroundColor Cyan

docker info *> $null
if ($LASTEXITCODE -ne 0) {
    Write-Host "Docker is not running. Please start Docker Desktop and try again." -ForegroundColor Red
    exit 1
}

docker compose up --build -d
if ($LASTEXITCODE -ne 0) {
    Write-Host "Failed to start containers. Check the output above." -ForegroundColor Red
    exit 1
}

Write-Host ""
Write-Host "Waiting for services to become healthy..." -ForegroundColor Yellow
$attempts = 0
while ($attempts -lt 30) {
    $webStatus = docker inspect payroll-web --format "{{.State.Health.Status}}" 2>$null
    if ($webStatus -eq "healthy") {
        break
    }
    Start-Sleep -Seconds 2
    $attempts++
}

Write-Host ""
Write-Host "Payroll app is running!" -ForegroundColor Green
Write-Host "  Login page: http://localhost:8082/login"
Write-Host "  API base:   http://localhost:8082/api"
Write-Host ""
Write-Host "Useful commands:"
Write-Host "  docker compose logs -f web   # view app logs"
Write-Host "  docker compose down          # stop containers"
