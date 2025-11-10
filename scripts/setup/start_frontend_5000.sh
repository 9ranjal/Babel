#!/bin/bash

# Start frontend on the standard Vite dev port (3000)
echo "🎨 Starting Babel Frontend on port 3000..."

cd /Users/pranjalsingh/Project\ Simple/frontend

# Install dependencies if needed
if [ ! -d "node_modules" ]; then
    echo "📦 Installing dependencies..."
    npm install
fi

# Start the Vite development server with explicit host/port
echo "🌐 Starting Vite dev server on http://localhost:3000"
npm run dev -- --host --port 3000

echo "✅ Frontend server started on http://localhost:3000"
