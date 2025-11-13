"""
LoreGuard Document Processing Service Health Monitoring

Health check service for monitoring system components and dependencies.
"""

import asyncio
import logging
from datetime import datetime
from typing import Dict, Any

from app.core.config import settings
from app.schemas.document import ServiceHealth


logger = logging.getLogger(__name__)


class HealthService:
    """Service for monitoring system health and dependencies."""
    
    def __init__(self):
        self.service_name = settings.SERVICE_NAME
        self.service_version = settings.SERVICE_VERSION
        
    async def get_health_status(self) -> Dict[str, Any]:
        """Get comprehensive health status of the service."""
        
        timestamp = datetime.utcnow()
        
        # Check all components
        checks = await asyncio.gather(
            self._check_database(),
            self._check_redis(),
            self._check_storage(),
            self._check_ocr_capability(),
            self._check_language_detection(),
            return_exceptions=True
        )
        
        database_ok, redis_ok, storage_ok, ocr_ok, lang_detect_ok = checks
        
        # Handle exceptions
        database_connected = database_ok if isinstance(database_ok, bool) else False
        redis_connected = redis_ok if isinstance(redis_ok, bool) else False
        storage_connected = storage_ok if isinstance(storage_ok, bool) else False
        ocr_available = ocr_ok if isinstance(ocr_ok, bool) else False
        language_detection_available = lang_detect_ok if isinstance(lang_detect_ok, bool) else False
        
        # Determine overall status
        critical_components = [database_connected, redis_connected]
        optional_components = [storage_connected, ocr_available, language_detection_available]
        
        if all(critical_components):
            if all(optional_components):
                status = "healthy"
            else:
                status = "degraded"
        else:
            status = "unhealthy"
        
        # Get processing metrics
        active_jobs, queue_size = await self._get_processing_metrics()
        
        return {
            "status": status,
            "service": self.service_name,
            "version": self.service_version,
            "timestamp": timestamp.isoformat(),
            "database_connected": database_connected,
            "redis_connected": redis_connected,
            "storage_connected": storage_connected,
            "ocr_available": ocr_available,
            "language_detection_available": language_detection_available,
            "active_processing_jobs": active_jobs,
            "queue_size": queue_size,
        }
    
    async def _check_database(self) -> bool:
        """Check database connectivity."""
        try:
            # Use shared database engine for health checks
            from app.db.database import get_engine
            from sqlalchemy import text
            
            engine = get_engine()
            with engine.connect() as conn:
                result = conn.execute(text("SELECT 1"))
                return result.scalar() == 1
                
        except Exception as e:
            logger.warning(f"Database health check failed: {e}")
            return False
    
    async def _check_redis(self) -> bool:
        """Check Redis connectivity."""
        try:
            import redis.asyncio as redis
            
            redis_client = redis.from_url(settings.REDIS_URL)
            await redis_client.ping()
            await redis_client.close()
            return True
            
        except Exception as e:
            logger.warning(f"Redis health check failed: {e}")
            return False
    
    async def _check_storage(self) -> bool:
        """Check object storage connectivity."""
        try:
            import boto3
            from botocore.exceptions import ClientError
            
            s3_client = boto3.client(
                's3',
                endpoint_url=settings.S3_ENDPOINT_URL,
                aws_access_key_id=settings.S3_ACCESS_KEY_ID,
                aws_secret_access_key=settings.S3_SECRET_ACCESS_KEY,
                region_name=settings.S3_REGION
            )
            
            # Try to list buckets
            s3_client.list_buckets()
            return True
            
        except Exception as e:
            logger.warning(f"Storage health check failed: {e}")
            return False
    
    async def _check_ocr_capability(self) -> bool:
        """Check OCR capability availability."""
        try:
            import pytesseract
            
            # Check if tesseract is available
            version = pytesseract.get_tesseract_version()
            return version is not None
            
        except Exception as e:
            logger.warning(f"OCR capability check failed: {e}")
            return False
    
    async def _check_language_detection(self) -> bool:
        """Check language detection capability."""
        try:
            from langdetect import detect
            
            # Test with a simple English phrase
            detected = detect("This is a test sentence in English.")
            return detected == "en"
            
        except Exception as e:
            logger.warning(f"Language detection check failed: {e}")
            return False
    
    async def _get_processing_metrics(self) -> tuple[int, int]:
        """Get current processing metrics."""
        try:
            # TODO: Implement actual metrics collection
            # For now, return dummy values
            active_jobs = 0
            queue_size = 0
            
            return active_jobs, queue_size
            
        except Exception as e:
            logger.warning(f"Failed to get processing metrics: {e}")
            return 0, 0

