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

# Install dependencies if needed
if ! python -c "import fastapi" 2>/dev/null; then
    echo "Installing backend dependencies..."
    pip install -r requirements.txt
    echo "Installing Playwright browsers..."
    playwright install chromium
fi

# Start server
echo "Starting FastAPI backend on http://localhost:8000"
echo "API docs available at http://localhost:8000/docs"
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
