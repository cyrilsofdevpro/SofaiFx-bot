#!/bin/bash

# MT5 Execution Service Runner for Linux/Mac
# This script starts the automated trading execution service

echo ""
echo "==============================================================================="
echo " SofAi FX - MT5 Execution Service"
echo "==============================================================================="
echo ""

# Check if Python is installed
if ! command -v python3 &> /dev/null; then
    echo "ERROR: Python 3 is not installed!"
    echo "Please install Python 3.8+ using:"
    echo "  Ubuntu/Debian: sudo apt-get install python3 python3-pip"
    echo "  macOS: brew install python3"
    exit 1
fi

# Check if .env file exists
if [ ! -f ".env" ]; then
    echo "ERROR: .env file not found!"
    echo ""
    echo "Please create a .env file with your MT5 credentials:"
    echo "  MT5_ACCOUNT=your_account"
    echo "  MT5_PASSWORD=your_password"
    echo "  MT5_SERVER=ICMarkets-Demo"
    echo ""
    exit 1
fi

echo "Starting MT5 Execution Service..."
echo ""

# Run the execution service
python3 run_execution_service.py

# If the script exits, show exit code
EXIT_CODE=$?
echo ""
echo "Service stopped with exit code: $EXIT_CODE"
if [ $EXIT_CODE -ne 0 ]; then
    echo ""
    echo "Check the logs in backend/execution/logs/ for details"
fi

exit $EXIT_CODE
