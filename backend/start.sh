#!/bin/bash

echo "🚀 Starting FastAPI + Celery application..."

# Kill existing Celery workers
echo "🧹 Cleaning up existing Celery workers..."
pkill -f "celery.*worker" 2>/dev/null || true

# Clear Python cache
echo "🧹 Clearing Python cache..."
find . -name "__pycache__" -type d -exec rm -rf {} + 2>/dev/null || true
find . -name "*.pyc" -delete 2>/dev/null || true

# Check if Redis is running
if ! redis-cli ping > /dev/null 2>&1; then
    echo "❌ Redis is not running. Please start Redis first:"
    echo "   brew services start redis"
    exit 1
fi

echo "🔄 Restarting Redis..."
brew services restart redis
sleep 2

echo "✅ Redis is running"

# Check if we're in Poetry environment
if ! poetry env info > /dev/null 2>&1; then
    echo "❌ Poetry environment not found. Please run 'poetry install' first."
    exit 1
fi

echo "✅ Poetry environment ready"

# Start Celery worker in background
echo "🔄 Starting fresh Celery worker..."
poetry run celery -A celery_app worker -l INFO &
CELERY_PID=$!

# Wait a moment for Celery to start
sleep 3

# Start FastAPI server
echo "🌐 Starting FastAPI server on http://localhost:8000"
echo "📚 API docs available at http://localhost:8000/docs"
echo ""
echo "Press Ctrl+C to stop all services"

# Trap Ctrl+C to clean up processes
trap 'echo ""; echo "🛑 Stopping services..."; kill $CELERY_PID 2>/dev/null; pkill -f "celery.*worker" 2>/dev/null; exit 0' INT

poetry run uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
