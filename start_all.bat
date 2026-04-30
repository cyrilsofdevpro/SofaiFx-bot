@echo off
cd /d "%~dp0"
echo Starting SofAi-FX Auto Trading Bot...
echo.

REM Start Flask API in one window
echo [1/2] Starting Flask API on http://localhost:5000
start "Flask API" cmd /k "cd backend && python -m src.api.flask_app"

REM Wait 3 seconds for API to start
timeout /t 3 /nobreak

REM Start Execution Service in another window
echo [2/2] Starting MT5 Execution Service (polling every 30 seconds)
start "Execution Service" cmd /k "cd backend && python run_execution_service.py"

echo.
echo ===================================================
echo Both services started!
echo.
echo Flask API: http://localhost:5000
echo Execution Service: Polling for signals every 30 seconds
echo MT5 Account: 2002073009 (JustMarkets-Demo)
echo.
echo Signals will auto-execute when detected.
echo Watch the "Execution Service" window for trade logs.
echo ===================================================
