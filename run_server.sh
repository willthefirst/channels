#!/bin/bash

# Clear the terminal
clear

# Print header
echo "========================================================"
echo "  Starting Synchronized Video Streaming Server"
echo "========================================================"

# Check if Python and required packages are available
echo "Checking Python environment..."
if ! command -v python &> /dev/null; then
    echo "❌ Python not found! Please install Python 3.7 or higher."
    exit 1
fi

# Create directories if they don't exist
echo "Checking directories..."
mkdir -p static uploads browser

# Count videos
STATIC_VIDEOS=$(find static -type f \( -name "*.mp4" -o -name "*.webm" -o -name "*.ogg" -o -name "*.mov" \) | wc -l)
UPLOAD_VIDEOS=$(find uploads -type f \( -name "*.mp4" -o -name "*.webm" -o -name "*.ogg" -o -name "*.mov" \) | wc -l)
TOTAL_VIDEOS=$((STATIC_VIDEOS + UPLOAD_VIDEOS))

echo "Found $TOTAL_VIDEOS videos ($STATIC_VIDEOS in static, $UPLOAD_VIDEOS in uploads)"

# Try to run the server
echo "Starting server..."
echo "------------------------------------------------------"
echo "🌐 Server will be available at: http://localhost:8000"
echo "------------------------------------------------------"
python main.py

# If we get here, the server has stopped
echo "------------------------------------------------------"
echo "Server stopped." 