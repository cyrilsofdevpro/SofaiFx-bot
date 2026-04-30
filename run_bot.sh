#!/bin/bash
# SofAi FX Bot Startup Script for macOS/Linux

echo ""
echo "===================================="
echo "  SofAi FX Trading Bot Launcher"
echo "===================================="
echo ""

# Check if Python is installed
if ! command -v python3 &> /dev/null; then
    echo "ERROR: Python 3 is not installed"
    echo "Please install Python 3.8+ from https://www.python.org"
    exit 1
fi

# Create virtual environment if it doesn't exist
if [ ! -d "backend/venv" ]; then
    echo "Creating virtual environment..."
    python3 -m venv backend/venv
fi

# Activate virtual environment
source backend/venv/bin/activate

# Install requirements
echo "Installing dependencies..."
pip install -q -r backend/requirements.txt

# Check if .env exists
if [ ! -f "backend/.env" ]; then
    echo ""
    echo "WARNING: .env file not found!"
    echo "Please copy .env.example to .env and configure your API keys:"
    echo "  - ALPHA_VANTAGE_API_KEY"
    echo "  - TELEGRAM_BOT_TOKEN"
    echo "  - TELEGRAM_CHAT_ID"
    echo "  - SENDER_EMAIL and SENDER_PASSWORD"
    echo ""
    read -p "Press Enter to continue..."
fi

# Start the bot
echo ""
echo "Starting SofAi FX Bot..."
echo ""
python backend/main.py
