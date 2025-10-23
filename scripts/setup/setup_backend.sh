#!/bin/bash
# Backend Setup Script for Termcraft AI

echo "🚀 Setting up Termcraft AI Backend..."
echo ""

cd "$(dirname "$0")/backend"

# Remove old venv if it exists
if [ -d "venv" ]; then
    echo "📦 Removing old virtual environment..."
    rm -rf venv
fi

# Create new venv
echo "📦 Creating virtual environment..."
python3 -m venv venv

# Activate venv
echo "✅ Activating virtual environment..."
source venv/bin/activate

# Upgrade pip
echo "📦 Upgrading pip..."
pip3 install --upgrade pip

# Install dependencies
echo "📦 Installing dependencies..."
pip3 install fastapi uvicorn[standard] supabase pydantic python-dotenv pydantic-settings

# Verify installation
echo ""
echo "✅ Verifying installation..."
python3 -c "import fastapi, uvicorn, supabase; print('✅ All packages installed successfully!')"

echo ""
echo "🎉 Backend setup complete!"
echo ""
echo "To start the backend server:"
echo "  cd backend"
echo "  source venv/bin/activate"
echo "  uvicorn api.main:app --reload --port 8000"
echo ""

