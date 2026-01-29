#!/bin/bash
# Start FastAPI backend server

cd "$(dirname "$0")/backend"

# Check if virtual environment exists
if [ ! -d "../.env" ]; then
    echo "Creating virtual environment..."
    python3 -m venv ../.env
fi

# Activate virtual environment
source ../.env/bin/activate

# Install/Update dependencies
echo "Ensuring all backend dependencies are installed..."
pip install -r requirements.txt
echo "Installing Playwright browsers..."
playwright install chromium

# Start server
echo "Starting FastAPI backend on http://localhost:8000"
echo "API docs available at http://localhost:8000/docs"
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
