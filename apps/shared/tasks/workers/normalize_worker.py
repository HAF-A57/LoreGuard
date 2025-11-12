#!/usr/bin/env python
"""
Celery worker for normalization tasks
Run with: celery -A apps.shared.tasks.celery_app worker --queue=normalize_queue --concurrency=5
"""

import sys
import os
from pathlib import Path

# Add project root to path
project_root = Path(__file__).resolve().parent.parent.parent.parent.parent
sys.path.insert(0, str(project_root))

from apps.shared.tasks.celery_app import celery_app

if __name__ == '__main__':
    celery_app.worker_main([
        'worker',
        '--queue=normalize_queue',
        '--concurrency=5',
        '--loglevel=info',
        '--max-tasks-per-child=50',
        '--time-limit=300',
        '--soft-time-limit=240',
    ])

