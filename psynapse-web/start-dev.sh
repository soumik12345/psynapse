#!/bin/bash

# Development startup script for Psynapse Web

echo "🚀 Starting Psynapse Web Development Environment"
echo ""

# Check if node_modules exists
if [ ! -d "node_modules" ]; then
    echo "📦 Installing dependencies..."
    npm install
    echo ""
fi

# Check if backend is running
echo "🔍 Checking backend connection..."
if curl -s http://localhost:8000/health > /dev/null 2>&1; then
    echo "✅ Backend is running on http://localhost:8000"
else
    echo "⚠️  Backend is not running!"
    echo ""
    echo "Please start the backend in another terminal:"
    echo "  cd .."
    echo "  uv run uvicorn psynapse.backend.server:app --reload"
    echo ""
    echo "Press Ctrl+C to exit, or wait 5 seconds to continue anyway..."
    sleep 5
fi

echo ""
echo "🌐 Starting web frontend..."
echo "   The app will open at http://localhost:3000"
echo ""

npm start

