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

# Start backend in background
echo "🚀 Starting streamer backend"
cd "$(dirname "$0")"
uv run main.py &
BACKEND_PID=$!

# Wait a moment for backend to start


echo ""
echo "✅ Radio Streamer is now running!"
echo "================================="
echo "Press Ctrl+C to stop the services."

# Wait for Ctrl+C
trap 'echo "🛑 Stopping services..."; kill $BACKEND_PID; exit' INT
wait
