@echo off
REM Start Flask API Server for Windows

echo.
echo Starting Flask API Server...
echo.

REM Check if virtual environment exists
if not exist "venv" (
    echo Creating virtual environment...
    python -m venv venv
)

REM Activate virtual environment
call venv\Scripts\activate.bat

REM Install requirements
pip install -q -r requirements.txt

REM Start Flask server
echo.
echo Flask server starting on http://localhost:5000
echo Dashboard: Open frontend/index.html in your browser
echo.
python -m src.api.flask_app

pause
