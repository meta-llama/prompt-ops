#!/bin/bash

# Development script for llama-prompt-ops frontend
# This script starts both the backend API and frontend development servers

# Start the FastAPI backend
echo "Starting llama-prompt-ops frontend backend (FastAPI)..."
cd backend
python -m uvicorn main:app --reload --port 8000 &
BACKEND_PID=$!

# Go back to project root
cd ..

# Start the React frontend
echo "Starting llama-prompt-ops frontend (React + Vite)..."
npm run dev &
FRONTEND_PID=$!

# Function to handle script termination
function cleanup {
  echo "Stopping development servers..."
  kill $BACKEND_PID
  kill $FRONTEND_PID
  exit
}

# Set up trap to catch termination signal
trap cleanup SIGINT

# Keep script running
echo "Development servers running:"
echo "  Backend:  http://localhost:8000"
echo "  Frontend: http://localhost:8080"
echo "Press Ctrl+C to stop all servers."
wait
