@echo off
REM SofAi FX Bot Startup Script for Windows

echo.
echo ====================================
echo   SofAi FX Trading Bot Launcher
echo ====================================
echo.

REM Check if Python is installed
python --version >nul 2>&1
if errorlevel 1 (
    echo ERROR: Python is not installed or not in PATH
    echo Please install Python 3.8+ from https://www.python.org
    pause
    exit /b 1
)

REM Check if virtual environment exists
if not exist "backend\venv" (
    echo Creating virtual environment...
    python -m venv backend\venv
)

REM Activate virtual environment
call backend\venv\Scripts\activate.bat

REM Install requirements
echo Installing dependencies...
pip install -q -r backend\requirements.txt

REM Check if .env exists
if not exist "backend\.env" (
    echo.
    echo WARNING: .env file not found!
    echo Please copy .env.example to .env and configure your API keys:
    echo   - ALPHA_VANTAGE_API_KEY
    echo   - TELEGRAM_BOT_TOKEN
    echo   - TELEGRAM_CHAT_ID
    echo   - SENDER_EMAIL and SENDER_PASSWORD
    echo.
    pause
)

REM Start the bot
echo.
echo Starting SofAi FX Bot...
echo.
python backend\main.py

pause
