#!/bin/bash
# Start React frontend server

cd "$(dirname "$0")/frontend"

# Check if node_modules exists
if [ ! -d "node_modules" ]; then
    echo "Installing frontend dependencies..."
    npm install
fi

# Start dev server
echo "Starting React frontend on http://localhost:5173"
npm run dev
