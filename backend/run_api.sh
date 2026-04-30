#!/bin/bash
# Start Flask API Server for macOS/Linux

echo ""
echo "Starting Flask API Server..."
echo ""

# Create virtual environment if it doesn't exist
if [ ! -d "venv" ]; then
    echo "Creating virtual environment..."
    python3 -m venv venv
fi

# Activate virtual environment
source venv/bin/activate

# Install requirements
pip install -q -r requirements.txt

# Start Flask server
echo ""
echo "Flask server starting on http://localhost:5000"
echo "Dashboard: Open frontend/index.html in your browser"
echo ""
python -m src.api.flask_app
