@echo off
REM MT5 Execution Service Runner for Windows
REM This script starts the automated trading execution service

echo.
echo ===============================================================================
echo  SofAi FX - MT5 Execution Service
echo ===============================================================================
echo.

REM Check if Python is installed
python --version >nul 2>&1
if errorlevel 1 (
    echo ERROR: Python is not installed or not in PATH
    echo Please install Python 3.8+ and add it to your PATH
    pause
    exit /b 1
)

REM Check if .env file exists
if not exist ".env" (
    echo ERROR: .env file not found!
    echo.
    echo Please create a .env file with your MT5 credentials:
    echo   MT5_ACCOUNT=your_account
    echo   MT5_PASSWORD=your_password
    echo   MT5_SERVER=ICMarkets-Demo
    echo.
    pause
    exit /b 1
)

echo Starting MT5 Execution Service...
echo.

REM Run the execution service
python run_execution_service.py

REM If the script exits, show exit code
echo.
echo Service stopped with exit code: %ERRORLEVEL%
if %ERRORLEVEL% neq 0 (
    echo.
    echo Check the logs in backend/execution/logs/ for details
)

pause
