#!/bin/bash

# Start TermCraft Backend on Port 5002
echo "🚀 Starting TermCraft Backend on port 5002..."

cd /Users/pranjalsingh/Project\ Simple/backend

# Activate virtual environment if it exists
if [ -d "venv" ]; then
    echo "📦 Activating virtual environment..."
    source venv/bin/activate
fi

# Start the FastAPI server
echo "🌐 Starting FastAPI server on http://localhost:5002"
python -m uvicorn api.main:app --reload --host 0.0.0.0 --port 5002

echo "✅ Backend server started on http://localhost:5002"
