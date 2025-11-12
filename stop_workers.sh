#!/bin/bash
# Script to stop Celery workers

set -e

PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$PROJECT_ROOT"

echo "Stopping LoreGuard Celery Workers..."
echo "===================================="

# Stop normalization worker
if [ -f "logs/normalize_worker.pid" ]; then
    PID=$(cat logs/normalize_worker.pid)
    if ps -p $PID > /dev/null 2>&1; then
        echo "Stopping normalization worker (PID: $PID)..."
        kill $PID
        rm logs/normalize_worker.pid
        echo "✅ Normalization worker stopped"
    else
        echo "⚠️  Normalization worker PID file exists but process not running"
        rm logs/normalize_worker.pid
    fi
else
    echo "⚠️  Normalization worker PID file not found"
fi

# Stop evaluation worker
if [ -f "logs/evaluate_worker.pid" ]; then
    PID=$(cat logs/evaluate_worker.pid)
    if ps -p $PID > /dev/null 2>&1; then
        echo "Stopping evaluation worker (PID: $PID)..."
        kill $PID
        rm logs/evaluate_worker.pid
        echo "✅ Evaluation worker stopped"
    else
        echo "⚠️  Evaluation worker PID file exists but process not running"
        rm logs/evaluate_worker.pid
    fi
else
    echo "⚠️  Evaluation worker PID file not found"
fi

# Also try to stop any remaining celery processes
pkill -f "celery.*normalize_queue" || true
pkill -f "celery.*evaluate_queue" || true

echo ""
echo "Workers stopped!"

