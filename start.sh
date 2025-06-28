#!/bin/bash

# Radio Streamer - Start Script
# Starts both the backend API and frontend simultaneously

echo "🎵 Starting Radio Streamer..."
echo "================================="

# Check if uv is available for the backend
if ! command -v uv &> /dev/null; then
    echo "❌ Error: 'uv' is not installed. Please install it first:"
    echo "   curl -LsSf https://astral.sh/uv/install.sh | sh"
    exit 1
fi

# Check if npm is available for the frontend
if ! command -v npm &> /dev/null; then
    echo "❌ Error: 'npm' is not installed. Please install Node.js first."
    exit 1
fi

# Start backend in background
echo "🚀 Starting backend API on http://0.0.0.0:8000 (accessible via raspberrypi.local:8000)..."
cd "$(dirname "$0")"
uv run main.py &
BACKEND_PID=$!

# Wait a moment for backend to start
sleep 3

# Start frontend in production mode
echo "🎨 Building and starting frontend in production mode..."
cd radio-frontend

# Check if node_modules exists, if not install dependencies
if [ ! -d "node_modules" ]; then
    echo "📦 Installing frontend dependencies..."
    npm install
fi

# Build the frontend for production
echo "🔨 Building frontend for production..."
npm run build

# Start the production server
echo "🚀 Starting frontend production server on http://0.0.0.0:4173 (accessible via raspberrypi.local:4173)..."
npm run preview &
FRONTEND_PID=$!

echo ""
echo "✅ Radio Streamer is now running!"
echo "🎵 Frontend: http://raspberrypi.local:4173"
echo "🔌 Backend API: http://raspberrypi.local:8000"
echo "📚 API Docs: http://raspberrypi.local:8000/docs"
echo ""
echo "Press Ctrl+C to stop both services"

# Wait for Ctrl+C
trap 'echo "🛑 Stopping services..."; kill $BACKEND_PID $FRONTEND_PID; exit' INT
wait
