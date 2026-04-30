# Start SofAi-FX Auto Trading Bot
Write-Host "Starting SofAi-FX Auto Trading Bot..." -ForegroundColor Green
Write-Host ""

# Activate venv if not already activated
if (-not $env:VIRTUAL_ENV) {
    Write-Host "[SETUP] Activating Python virtual environment..." -ForegroundColor Cyan
    & "c:\Users\Cyril Sofdev\Desktop\SofAi-Fx\.venv\Scripts\Activate.ps1"
}

# Start Flask API in background job
Write-Host "[1/2] Starting Flask API on http://localhost:5000" -ForegroundColor Yellow
$flaskJob = Start-Job -ScriptBlock {
    cd "c:\Users\Cyril Sofdev\Desktop\SofAi-Fx\backend"
    python -m src.api.flask_app
} -Name "Flask-API"

# Wait for API to start
Write-Host "Waiting for Flask API to initialize..." -ForegroundColor Gray
Start-Sleep -Seconds 3

# Start Execution Service in background job
Write-Host "[2/2] Starting MT5 Execution Service (polling every 30 seconds)" -ForegroundColor Yellow
$execJob = Start-Job -ScriptBlock {
    cd "c:\Users\Cyril Sofdev\Desktop\SofAi-Fx\backend"
    python run_execution_service.py
} -Name "Execution-Service"

Write-Host ""
Write-Host "===================================================" -ForegroundColor Green
Write-Host "Both services started!" -ForegroundColor Green
Write-Host ""
Write-Host "Flask API:         http://localhost:5000" -ForegroundColor Cyan
Write-Host "Execution Service: Polling every 30 seconds" -ForegroundColor Cyan
Write-Host "MT5 Account:       2002073009 (JustMarkets-Demo)" -ForegroundColor Cyan
Write-Host ""
Write-Host "Signals will auto-execute when detected." -ForegroundColor Yellow
Write-Host "Monitor logs below:" -ForegroundColor Yellow
Write-Host "===================================================" -ForegroundColor Green
Write-Host ""

# Show logs from both jobs
Write-Host "Running both services. Press Ctrl+C to stop all." -ForegroundColor Yellow
Write-Host ""

# Keep showing output
while ($true) {
    $flaskOutput = Receive-Job -Job $flaskJob -Keep 2>$null
    $execOutput = Receive-Job -Job $execJob -Keep 2>$null
    
    if ($flaskOutput) { Write-Host $flaskOutput }
    if ($execOutput) { Write-Host $execOutput }
    
    Start-Sleep -Milliseconds 500
}
