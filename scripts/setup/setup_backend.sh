#!/bin/bash
# Backend Setup Script for Babel AI (consolidated virtualenv)

set -e

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/../.." && pwd)"

echo "🚀 Setting up Babel AI backend inside project virtual environment..."
echo ""

cd "$PROJECT_ROOT"

# Ensure only the project-level virtual environment exists
if [ -d "backend/venv" ]; then
    echo "🧹 Removing legacy backend/venv virtual environment..."
    rm -rf backend/venv
fi

if [ ! -d ".venv" ]; then
    echo "📦 Creating project virtual environment at .venv ..."
    python3 -m venv .venv
else
    echo "✅ Reusing existing project virtual environment (.venv)"
fi

echo "🔌 Activating .venv ..."
source .venv/bin/activate

echo "⬆️  Upgrading pip ..."
python -m pip install --upgrade pip

echo "📦 Installing backend requirements ..."
python -m pip install -r backend/requirements.txt

echo ""
echo "✅ Backend setup complete inside .venv!"
echo ""
echo "To start the backend server:"
echo "  cd \"$PROJECT_ROOT\""
echo "  source .venv/bin/activate"
echo "  PYTHONPATH=backend uvicorn api.main:app --reload --host 0.0.0.0 --port 5002"
echo ""

