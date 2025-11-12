"""
Celery application configuration for LoreGuard task queues
"""

import os
import logging
from celery import Celery
from celery.schedules import crontab

logger = logging.getLogger(__name__)

# Get Redis connection details
LOREGUARD_HOST_IP = os.getenv('LOREGUARD_HOST_IP', 'localhost')
REDIS_PASSWORD = os.getenv('REDIS_PASSWORD', 'redis_password_here')

# Construct Redis URL if not explicitly provided
REDIS_URL = os.getenv('REDIS_URL')
if not REDIS_URL:
    # Build URL with password if provided
    if REDIS_PASSWORD:
        REDIS_URL = f'redis://:{REDIS_PASSWORD}@{LOREGUARD_HOST_IP}:6379/0'
    else:
        REDIS_URL = f'redis://{LOREGUARD_HOST_IP}:6379/0'

# Create Celery app
celery_app = Celery(
    'loreguard',
    broker=REDIS_URL,
    backend=REDIS_URL,  # Use Redis for result backend
    include=[
        'apps.shared.tasks.normalize_tasks',
        'apps.shared.tasks.evaluate_tasks',
    ]
)

# Celery configuration
celery_app.conf.update(
    # Task serialization
    task_serializer='json',
    accept_content=['json'],
    result_serializer='json',
    timezone='UTC',
    enable_utc=True,
    
    # Task routing
    task_routes={
        'apps.shared.tasks.normalize_tasks.*': {'queue': 'normalize_queue'},
        'apps.shared.tasks.evaluate_tasks.*': {'queue': 'evaluate_queue'},
    },
    
    # Task execution
    task_acks_late=True,  # Acknowledge after task completion
    task_reject_on_worker_lost=True,  # Reject tasks if worker dies
    task_time_limit=600,  # Hard time limit (10 minutes)
    task_soft_time_limit=540,  # Soft time limit (9 minutes)
    
    # Worker configuration
    worker_prefetch_multiplier=4,  # Prefetch 4 tasks per worker
    worker_max_tasks_per_child=50,  # Restart worker after 50 tasks (prevent memory leaks)
    
    # Retry configuration
    task_autoretry_for=(Exception,),
    task_retry_backoff=True,
    task_retry_backoff_max=600,  # Max 10 minutes between retries
    task_retry_jitter=True,  # Add randomness to retry delays
    task_max_retries=3,  # Max 3 retries
    
    # Result backend
    result_expires=3600,  # Results expire after 1 hour
    # Note: result_backend_transport_options only needed for Redis Sentinel
    # For regular Redis, these options are not needed
    
    # Queue configuration
    task_default_queue='default',
    task_default_exchange='tasks',
    task_default_exchange_type='direct',
    task_default_routing_key='default',
    
    # Monitoring
    worker_send_task_events=True,
    task_send_sent_event=True,
)

# Log configuration
logger.info(f"Celery app configured with broker: {REDIS_URL}")

