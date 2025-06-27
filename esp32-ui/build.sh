#!/bin/bash

# ESP32 Radio UI Build Script
echo "Building ESP32 Radio Streamer UI..."

# Check if PlatformIO is available
if ! command -v pio &> /dev/null; then
    echo "Error: PlatformIO is not installed or not in PATH"
    echo "Please install PlatformIO: https://platformio.org/install"
    exit 1
fi

# Build the project
echo "Building project..."
pio run

if [ $? -eq 0 ]; then
    echo "Build successful!"
    echo ""
    echo "To upload to ESP32, run:"
    echo "  pio run --target upload"
    echo ""
    echo "To monitor serial output, run:"
    echo "  pio device monitor"
else
    echo "Build failed!"
    exit 1
fi
