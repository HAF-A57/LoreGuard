"""
Shared Celery task definitions for LoreGuard services
"""

from .celery_app import celery_app
from .normalize_tasks import normalize_artifact, batch_normalize_artifacts
from .evaluate_tasks import evaluate_artifact

__all__ = [
    'celery_app',
    'normalize_artifact',
    'batch_normalize_artifacts',
    'evaluate_artifact',
]

