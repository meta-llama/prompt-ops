#!/bin/bash

# Development script for llama-prompt-ops frontend
# This script starts both the backend API and frontend development servers

set -e  # Exit on any error

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Function to print colored output
print_color() {
    printf "${1}${2}${NC}\n"
}

# Function to check if a port is available
check_port() {
    local port=$1
    if lsof -Pi :$port -sTCP:LISTEN -t >/dev/null 2>&1; then
        return 1
    else
        return 0
    fi
}

# Function to handle script termination
cleanup() {
    print_color $YELLOW "Stopping development servers..."
    if [[ -n $BACKEND_PID ]]; then
        kill $BACKEND_PID 2>/dev/null || true
    fi
    if [[ -n $FRONTEND_PID ]]; then
        kill $FRONTEND_PID 2>/dev/null || true
    fi
    exit 0
}

# Set up trap to catch termination signal
trap cleanup SIGINT SIGTERM

print_color $GREEN "🚀 Starting llama-prompt-ops frontend development environment..."

# Check if we're in the right directory
if [[ ! -f "package.json" ]]; then
    print_color $RED "❌ Error: package.json not found. Please run this script from the frontend directory."
    exit 1
fi

# Check if node_modules exists
if [[ ! -d "node_modules" ]]; then
    print_color $YELLOW "📦 Installing frontend dependencies..."
    npm install
fi

# Check backend directory
if [[ ! -d "backend" ]]; then
    print_color $RED "❌ Error: backend directory not found."
    exit 1
fi

cd backend

# Check if virtual environment exists
if [[ ! -d "venv" ]]; then
    print_color $YELLOW "🐍 Creating Python virtual environment..."
    python -m venv venv
fi

# Activate virtual environment
source venv/bin/activate

# Check if requirements are installed
if [[ ! -f "venv/pyvenv.cfg" ]] || ! pip freeze | grep -q "fastapi"; then
    print_color $YELLOW "📦 Installing backend dependencies..."
    pip install -r requirements.txt
fi

# Check for .env file
if [[ ! -f ".env" ]]; then
    print_color $YELLOW "⚠️  No .env file found. Creating template..."
    cat > .env << 'EOF'
# OpenRouter API Key (Required)
# Get your key at: https://openrouter.ai/
OPENROUTER_API_KEY=your_openrouter_api_key_here

# OpenAI API Key (Optional)
# Only needed for the /enhance endpoint fallback functionality
OPENAI_API_KEY=your_openai_api_key_here
EOF
    print_color $RED "❌ Please edit backend/.env with your API keys before continuing."
    exit 1
fi

# Check if ports are available
if ! check_port 8000; then
    print_color $RED "❌ Port 8000 is already in use. Please free it or kill existing processes:"
    print_color $YELLOW "   pkill -f uvicorn"
    exit 1
fi

if ! check_port 8080; then
    print_color $RED "❌ Port 8080 is already in use. Please free it or kill existing processes:"
    print_color $YELLOW "   pkill -f vite"
    exit 1
fi

# Start the FastAPI backend
print_color $GREEN "🔧 Starting backend (FastAPI)..."
python -m uvicorn main:app --reload --port 8000 &
BACKEND_PID=$!

# Wait a moment for backend to start
sleep 2

# Go back to project root
cd ..

# Start the React frontend
print_color $GREEN "⚡ Starting frontend (React + Vite)..."
npm run dev &
FRONTEND_PID=$!

# Keep script running
print_color $GREEN "✅ Development servers running:"
print_color $GREEN "  👉 Frontend: http://localhost:8080"
print_color $GREEN "  👉 Backend:  http://localhost:8000"
print_color $GREEN "  👉 API Docs: http://localhost:8000/docs"
print_color $YELLOW "Press Ctrl+C to stop all servers."

# Wait for processes
wait
