#!/bin/bash

# TermCraft AI - Complete Startup Script
# Starts both backend (port 5001) and frontend (port 5000)

echo "🚀 Starting TermCraft AI Application..."
echo "================================================"

# Check if Ollama is running
echo "🔍 Checking Ollama server..."
if ! curl -s http://localhost:11434/api/tags > /dev/null 2>&1; then
    echo "⚠️  Ollama server not detected. Starting Ollama..."
    ollama serve &
    sleep 3
    echo "✅ Ollama server started"
else
    echo "✅ Ollama server is running"
fi

# Start Backend (Port 5002)
echo ""
echo "🔧 Starting Backend on port 5002..."
cd /Users/pranjalsingh/Project\ Simple/backend

# Activate virtual environment if it exists
if [ -d "venv" ]; then
    echo "📦 Activating virtual environment..."
    source venv/bin/activate
fi

# Start backend in background
echo "🌐 Starting FastAPI server on http://localhost:5002"
python -m uvicorn api.main:app --reload --host 0.0.0.0 --port 5002 &
BACKEND_PID=$!

# Wait a moment for backend to start
sleep 3

# Start Frontend (Port 5003)
echo ""
echo "🎨 Starting Frontend on port 5003..."
cd /Users/pranjalsingh/Project\ Simple/frontend

# Start frontend in background
echo "🌐 Starting Vite dev server on http://localhost:5003"
npm run dev &
FRONTEND_PID=$!

echo ""
echo "✅ TermCraft AI is now running!"
echo "================================================"
echo "🌐 Frontend: http://localhost:5003"
echo "🔧 Backend:  http://localhost:5002"
echo "🤖 Ollama:   http://localhost:11434"
echo ""
echo "Press Ctrl+C to stop all services"

# Function to cleanup on exit
cleanup() {
    echo ""
    echo "🛑 Stopping TermCraft AI services..."
    kill $BACKEND_PID $FRONTEND_PID 2>/dev/null
    echo "✅ All services stopped"
    exit 0
}

# Set up signal handlers
trap cleanup SIGINT SIGTERM

# Wait for user to stop
wait
