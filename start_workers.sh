#!/bin/bash
# Script to start Celery workers for LoreGuard

set -e

echo "Starting LoreGuard Celery Workers..."
echo "===================================="

# Check if Redis is running
if ! docker ps | grep -q loreguard-redis; then
    echo "❌ Redis container is not running!"
    echo "   Start with: docker-compose up -d redis"
    exit 1
fi

# Get project root
PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$PROJECT_ROOT"

# Check if virtual environment exists (optional)
if [ -d "venv" ]; then
    source venv/bin/activate
fi

# Start normalization worker in background
echo ""
echo "Starting normalization worker..."
celery -A apps.shared.tasks.celery_app worker \
    --queue=normalize_queue \
    --concurrency=5 \
    --loglevel=info \
    --max-tasks-per-child=50 \
    --time-limit=300 \
    --soft-time-limit=240 \
    --hostname=normalize-worker@%h \
    --logfile=logs/normalize_worker.log \
    --pidfile=logs/normalize_worker.pid \
    --detach

echo "✅ Normalization worker started (PID: $(cat logs/normalize_worker.pid 2>/dev/null || echo 'N/A'))"

# Start evaluation worker in background
echo ""
echo "Starting evaluation worker..."
celery -A apps.shared.tasks.celery_app worker \
    --queue=evaluate_queue \
    --concurrency=3 \
    --loglevel=info \
    --max-tasks-per-child=20 \
    --time-limit=600 \
    --soft-time-limit=540 \
    --hostname=evaluate-worker@%h \
    --logfile=logs/evaluate_worker.log \
    --pidfile=logs/evaluate_worker.pid \
    --detach

echo "✅ Evaluation worker started (PID: $(cat logs/evaluate_worker.pid 2>/dev/null || echo 'N/A'))"

echo ""
echo "Workers started successfully!"
echo ""
echo "To check status:"
echo "  celery -A apps.shared.tasks.celery_app inspect active"
echo ""
echo "To stop workers:"
echo "  ./stop_workers.sh"
echo ""
echo "To view logs:"
echo "  tail -f logs/normalize_worker.log"
echo "  tail -f logs/evaluate_worker.log"

