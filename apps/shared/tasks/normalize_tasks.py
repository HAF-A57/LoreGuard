"""
Normalization task definitions for Celery
"""

import logging
import sys
from pathlib import Path
from typing import List, Optional, Dict, Any

from .celery_app import celery_app

logger = logging.getLogger(__name__)

# Add project root and svc-normalize to path for imports
apps_dir = Path(__file__).resolve().parent.parent.parent.parent
project_root = apps_dir.parent
svc_normalize_path = apps_dir / 'svc-normalize' / 'app'

# Add paths in order: project root, then svc-normalize
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))
if str(svc_normalize_path) not in sys.path:
    sys.path.insert(0, str(svc_normalize_path))


@celery_app.task(
    name='apps.shared.tasks.normalize_tasks.normalize_artifact',
    bind=True,
    max_retries=3,
    default_retry_delay=60,  # 1 minute initial retry delay
    autoretry_for=(Exception,),
    retry_backoff=True,
    retry_backoff_max=600,  # Max 10 minutes between retries
    retry_jitter=True,
    time_limit=1800,  # 30 minute hard limit (increased for large files)
    soft_time_limit=1500,  # 25 minute soft limit (increased for large files)
)
def normalize_artifact(self, artifact_id: str, processing_options: Optional[Dict[str, Any]] = None):
    """
    Normalize an artifact by processing its content.
    
    This task fetches artifact content from storage, extracts text and metadata,
    stores normalized content, and updates the artifact record.
    
    Args:
        artifact_id: UUID of the artifact to normalize
        processing_options: Optional processing configuration
        
    Returns:
        Dict with processing results including normalized_ref and metadata
        
    Raises:
        ValueError: If artifact not found or invalid
        RuntimeError: If processing fails
    """
    try:
        # Import from normalize service - workers run in normalize container
        # The normalize service code is at /app/app in normalize container
        # Import directly from app.services since we're in the normalize container
        from app.services.document_processing_service import DocumentProcessingService
        import asyncio
        import os
        
        logger.info(f"Starting normalization task for artifact {artifact_id}")
        
        # Create service instance
        service = DocumentProcessingService()
        
        # Run async processing
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        try:
            result = loop.run_until_complete(
                service.process_artifact(
                    artifact_id=artifact_id,
                    processing_options=processing_options
                )
            )
            logger.info(f"Successfully normalized artifact {artifact_id}: {result.get('normalized_ref')}")
            return result
        finally:
            loop.close()
            # Note: No cleanup needed - service uses shared engine that persists
            
    except ValueError as e:
        # Don't retry for not found errors
        logger.error(f"Artifact {artifact_id} not found: {e}")
        raise
    except Exception as e:
        logger.error(f"Error normalizing artifact {artifact_id}: {e}", exc_info=True)
        # Check if we should retry
        if self.request.retries < self.max_retries:
            raise self.retry(exc=e)
        else:
            # Max retries reached, fail permanently
            logger.error(f"Max retries reached for artifact {artifact_id}, failing permanently")
            raise


@celery_app.task(
    name='apps.shared.tasks.normalize_tasks.batch_normalize_artifacts',
    bind=True,
    max_retries=2,
    default_retry_delay=120,
    time_limit=1800,  # 30 minute hard limit
    soft_time_limit=1500,  # 25 minute soft limit
)
def batch_normalize_artifacts(self, artifact_ids: List[str], processing_options: Optional[Dict[str, Any]] = None):
    """
    Normalize multiple artifacts in batch.
    
    This task processes multiple artifacts sequentially. For parallel processing,
    use individual normalize_artifact tasks.
    
    Args:
        artifact_ids: List of artifact UUIDs to normalize
        processing_options: Optional processing configuration
        
    Returns:
        Dict with results for each artifact
    """
    results = {
        'success': [],
        'failed': [],
        'total': len(artifact_ids)
    }
    
    logger.info(f"Starting batch normalization for {len(artifact_ids)} artifacts")
    
    for artifact_id in artifact_ids:
        try:
            result = normalize_artifact.apply(args=[artifact_id], kwargs={'processing_options': processing_options})
            results['success'].append({
                'artifact_id': artifact_id,
                'result': result.get() if result.ready() else None
            })
        except Exception as e:
            logger.error(f"Failed to normalize artifact {artifact_id}: {e}")
            results['failed'].append({
                'artifact_id': artifact_id,
                'error': str(e)
            })
    
    logger.info(f"Batch normalization complete: {len(results['success'])} success, {len(results['failed'])} failed")
    return results

