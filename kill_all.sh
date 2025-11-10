#!/bin/bash

echo "🔪 Killing all Babel-related processes..."

# Kill by process names
echo "Looking for processes by name..."
pkill -f "uvicorn.*api.main:app" 2>/dev/null && echo "✅ Killed uvicorn backend processes"
pkill -f "python.*api.workers.runner" 2>/dev/null && echo "✅ Killed worker runner processes"
pkill -f "vite" 2>/dev/null && echo "✅ Killed Vite frontend processes"
pkill -f "node.*vite" 2>/dev/null && echo "✅ Killed Node/Vite processes"

# Kill by common Babel ports
echo "Looking for processes on common Babel ports..."
for port in 3000 3001 5000 5001 5002 5003 5173 54321; do
    if lsof -ti:$port >/dev/null 2>&1; then
        echo "Killing process on port $port..."
        kill $(lsof -ti:$port) 2>/dev/null && echo "✅ Killed process on port $port"
    fi
done

# Kill any remaining Python processes in the project directory
echo "Looking for Python processes in project directory..."
pgrep -f "python.*Project Simple" | xargs kill 2>/dev/null && echo "✅ Killed Python processes in project directory"

# Kill any remaining Node processes in the project directory
echo "Looking for Node processes in project directory..."
pgrep -f "node.*Project Simple" | xargs kill 2>/dev/null && echo "✅ Killed Node processes in project directory"

echo "🧹 Cleanup complete! All Babel processes should be terminated."
echo ""
echo "Now you can safely restart with:"
echo "  make start-backend &"
echo "  make runner &"
echo "  make start-frontend &"
