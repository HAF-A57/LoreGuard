"""
Evaluation task definitions for Celery
"""

import logging
import sys
from pathlib import Path
from typing import Optional, Dict, Any

from .celery_app import celery_app

logger = logging.getLogger(__name__)

# Add project root and svc-api to path for imports
apps_dir = Path(__file__).resolve().parent.parent.parent.parent
project_root = apps_dir.parent
svc_api_path = apps_dir / 'svc-api' / 'app'

# Add paths in order: project root, then svc-api
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))
if str(svc_api_path) not in sys.path:
    sys.path.insert(0, str(svc_api_path))


@celery_app.task(
    name='apps.shared.tasks.evaluate_tasks.evaluate_artifact',
    bind=True,
    max_retries=3,
    default_retry_delay=120,  # 2 minute initial retry delay (LLM rate limits)
    autoretry_for=(Exception,),
    retry_backoff=True,
    retry_backoff_max=900,  # Max 15 minutes between retries (for LLM rate limits)
    retry_jitter=True,
    time_limit=600,  # 10 minute hard limit
    soft_time_limit=540,  # 9 minute soft limit
)
def evaluate_artifact(self, artifact_id: str, rubric_version: Optional[str] = None, provider_id: Optional[str] = None):
    """
    Evaluate an artifact against a rubric.
    
    This task runs LLM-based evaluation on a normalized artifact and stores
    the evaluation results.
    
    Args:
        artifact_id: UUID of the artifact to evaluate
        rubric_version: Optional rubric version (uses active/default if not provided)
        provider_id: Optional LLM provider ID (uses default/active if not provided)
        
    Returns:
        Dict with evaluation results
        
    Raises:
        ValueError: If artifact or rubric not found
        RuntimeError: If evaluation fails
    """
    try:
        # Import from API service - workers run in API container
        # The API service code is at /app/app in API container
        # Import directly from app.services since we're in the API container
        import sys
        import os
        
        # Ensure /app/app is in path for imports (API container's app directory)
        if '/app/app' not in sys.path:
            sys.path.insert(0, '/app/app')
        
        from app.services.llm_evaluation import LLMEvaluationService
        from sqlalchemy import create_engine
        from sqlalchemy.orm import sessionmaker
        import asyncio
        
        logger.info(f"Starting evaluation task for artifact {artifact_id}")
        
        # Create database session
        database_url = os.getenv('DATABASE_URL')
        if not database_url:
            raise RuntimeError("DATABASE_URL not configured")
        
        engine = create_engine(database_url)
        Session = sessionmaker(bind=engine)
        session = Session()
        
        try:
            # Create evaluation service
            evaluation_service = LLMEvaluationService(db=session)
            
            # Run async evaluation
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            try:
                evaluation = loop.run_until_complete(
                    evaluation_service.evaluate_artifact(
                        artifact_id=artifact_id,
                        rubric_version=rubric_version or "latest",
                        provider_id=provider_id,
                        db=session
                    )
                )
                
                logger.info(f"Successfully evaluated artifact {artifact_id}: {evaluation.label} (confidence: {evaluation.confidence})")
                return {
                    'artifact_id': artifact_id,
                    'evaluation_id': str(evaluation.id),
                    'label': evaluation.label,
                    'confidence': float(evaluation.confidence) if evaluation.confidence else None,
                    'total_score': evaluation.total_score,
                    'rubric_version': evaluation.rubric_version,
                    'status': 'completed'
                }
            finally:
                loop.close()
        finally:
            session.close()
            
    except ValueError as e:
        # Don't retry for not found errors
        logger.error(f"Artifact or rubric not found: {e}")
        raise
    except Exception as e:
        logger.error(f"Error evaluating artifact {artifact_id}: {e}", exc_info=True)
        # Check if we should retry
        if self.request.retries < self.max_retries:
            raise self.retry(exc=e)
        else:
            # Max retries reached, fail permanently
            logger.error(f"Max retries reached for artifact {artifact_id}, failing permanently")
            raise

