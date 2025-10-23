#!/bin/bash

# Start TermCraft Frontend on Port 5003
echo "🎨 Starting TermCraft Frontend on port 5003..."

cd /Users/pranjalsingh/Project\ Simple/frontend

# Install dependencies if needed
if [ ! -d "node_modules" ]; then
    echo "📦 Installing dependencies..."
    npm install
fi

# Start the Vite development server
echo "🌐 Starting Vite dev server on http://localhost:5003"
npm run dev

echo "✅ Frontend server started on http://localhost:5003"
