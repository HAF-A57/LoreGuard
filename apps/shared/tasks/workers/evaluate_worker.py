#!/usr/bin/env python
"""
Celery worker for evaluation tasks
Run with: celery -A apps.shared.tasks.celery_app worker --queue=evaluate_queue --concurrency=3
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
        '--queue=evaluate_queue',
        '--concurrency=3',
        '--loglevel=info',
        '--max-tasks-per-child=20',
        '--time-limit=600',
        '--soft-time-limit=540',
    ])

