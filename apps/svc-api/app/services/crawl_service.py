"""
Crawl Service for triggering and managing web crawls

Handles the orchestration of Scrapy spiders for source crawling.
Separates crawl logic from API endpoints for better maintainability.
"""

import subprocess
import os
import logging
import json
from typing import Dict, Any, Optional
from pathlib import Path
from datetime import datetime

from sqlalchemy.orm import Session
from models.job import Job
from models.source import Source
from core.config import settings

logger = logging.getLogger(__name__)


class CrawlService:
    """Service for managing crawl operations"""
    
    # Map source types to spider names
    SPIDER_MAP = {
        "web": "generic_web",
        "news": "news",
        "rss": "generic_web",  # RSS sources use generic web spider
        "feed": "generic_web",
        "api": "generic_web",  # API sources may need custom spider later
    }
    
    def __init__(self, ingestion_service_path: Optional[str] = None):
        """
        Initialize crawl service
        
        Args:
            ingestion_service_path: Path to ingestion service directory
                                   If None, auto-detects relative to API service
        """
        if ingestion_service_path:
            self.ingestion_path = Path(ingestion_service_path)
        else:
            # Auto-detect: go up from svc-api/app/services to app, then to svc-ingestion
            # In Docker: /app/app/services/crawl_service.py -> /app/svc-ingestion
            current_file = Path(__file__)
            self.ingestion_path = current_file.parent.parent.parent / "svc-ingestion"
        
        if not self.ingestion_path.exists():
            raise ValueError(f"Ingestion service path not found: {self.ingestion_path}")
    
    def trigger_crawl(
        self,
        source: Source,
        db: Session,
        job_id: Optional[str] = None
    ) -> Job:
        """
        Trigger a crawl for a source
        
        Args:
            source: Source model instance
            db: Database session
            job_id: Optional job ID (will create if not provided)
            
        Returns:
            Job instance tracking the crawl
            
        Raises:
            ValueError: If source configuration is invalid
            RuntimeError: If spider cannot be started
        """
        logger.info(f"[DEBUG] trigger_crawl called for source {source.id} ({source.name})")
        
        # Validate source configuration
        logger.info(f"[DEBUG] Validating source configuration...")
        self._validate_source_config(source)
        logger.info(f"[DEBUG] Source configuration valid")
        
        # Determine spider name from source type
        spider_name = self.SPIDER_MAP.get(source.type, "generic_web")
        logger.info(f"[DEBUG] Spider name: {spider_name}")
        
        # Extract crawl configuration from source.config
        config = source.config or {}
        crawl_config = config.get("crawl_scope", {})
        filtering_config = config.get("filtering", {})
        
        # Get start URLs from config
        start_urls = config.get("start_urls", [])
        if not start_urls:
            raise ValueError(f"Source {source.id} has no start_urls configured")
        logger.info(f"[DEBUG] Start URLs: {start_urls}")
        
        # Create or use existing job
        if job_id:
            logger.info(f"[DEBUG] Using existing job: {job_id}")
            job = db.query(Job).filter(Job.id == job_id).first()
            if not job:
                raise ValueError(f"Job {job_id} not found")
        else:
            logger.info(f"[DEBUG] Creating new job...")
            job = Job(
                type="ingest",
                status="pending",
                payload={
                    "source_id": str(source.id),
                    "source_name": source.name,
                    "source_type": source.type,
                    "spider_name": spider_name,
                }
            )
            logger.info(f"[DEBUG] Adding timeline entry...")
            job.add_timeline_entry("pending", "Crawl job created")
            logger.info(f"[DEBUG] Adding job to session...")
            db.add(job)
            logger.info(f"[DEBUG] Committing job to database...")
            db.commit()
            logger.info(f"[DEBUG] Refreshing job from database...")
            db.refresh(job)
            logger.info(f"[DEBUG] Job created with ID: {job.id}")
        
        # Build Scrapy command
        logger.info(f"[DEBUG] Building Scrapy command...")
        max_artifacts = crawl_config.get("max_artifacts", 0)
        max_depth = crawl_config.get("max_depth", 3)
        logger.info(f"[DEBUG] Crawl limits: max_depth={max_depth}, max_artifacts={max_artifacts}")
        
        scrapy_cmd = self._build_scrapy_command(
            spider_name=spider_name,
            source_id=str(source.id),
            job_id=job.id,
            start_urls=start_urls,
            max_depth=max_depth,
            max_artifacts=max_artifacts,
            allowed_domains=filtering_config.get("allowed_domains", [])
        )
        logger.info(f"[DEBUG] Scrapy command: {' '.join(scrapy_cmd)}")
        
        # Start spider process
        try:
            logger.info(f"[DEBUG] Calling _start_spider_process...")
            process = self._start_spider_process(scrapy_cmd)
            logger.info(f"[DEBUG] Process object returned: {process}, PID: {process.pid if process else 'None'}")
            
            if not process:
                raise RuntimeError("_start_spider_process returned None")
            
            # Update job with process info
            logger.info(f"[DEBUG] Updating job with process info (PID: {process.pid})...")
            job.status = "running"
            # Create new dict to trigger SQLAlchemy change detection for JSON column
            updated_payload = dict(job.payload) if job.payload else {}
            updated_payload["process_id"] = process.pid
            updated_payload["command"] = " ".join(scrapy_cmd)
            job.payload = updated_payload
            logger.info(f"[DEBUG] Adding timeline entry for running status...")
            job.add_timeline_entry("running", f"Spider started with PID {process.pid}")
            logger.info(f"[DEBUG] Committing job updates to database...")
            db.commit()
            db.refresh(job)  # Refresh to ensure we have the committed state
            logger.info(f"[DEBUG] Job committed and refreshed successfully")
            
            logger.info(
                f"Started crawl for source {source.id} "
                f"(job {job.id}, spider {spider_name}, PID {process.pid})"
            )
            
            return job
            
        except Exception as e:
            # Update job with error
            logger.error(f"[DEBUG] Exception caught: {type(e).__name__}: {e}")
            logger.error(f"[DEBUG] Updating job with error status...")
            job.status = "failed"
            job.error = str(e)
            job.add_timeline_entry("failed", f"Failed to start spider: {e}")
            logger.info(f"[DEBUG] Committing failed job status...")
            db.commit()
            logger.info(f"[DEBUG] Failed job committed")
            
            logger.error(f"Failed to start crawl for source {source.id}: {e}")
            raise RuntimeError(f"Failed to start spider: {e}") from e
    
    def _validate_source_config(self, source: Source) -> None:
        """Validate source configuration before crawling"""
        if not source.config:
            raise ValueError(f"Source {source.id} has no configuration")
        
        config = source.config
        start_urls = config.get("start_urls", [])
        
        if not start_urls:
            raise ValueError(f"Source {source.id} has no start_urls in configuration")
        
        if not isinstance(start_urls, list):
            raise ValueError(f"Source {source.id} start_urls must be a list")
        
        if len(start_urls) == 0:
            raise ValueError(f"Source {source.id} start_urls list is empty")
    
    def _build_scrapy_command(
        self,
        spider_name: str,
        source_id: str,
        job_id: str,
        start_urls: list,
        max_depth: int = 3,
        max_artifacts: int = 0,
        allowed_domains: list = None
    ) -> list:
        """
        Build Scrapy command arguments
        
        Args:
            spider_name: Name of spider to run
            source_id: Source ID
            job_id: Job ID
            start_urls: List of start URLs
            max_depth: Maximum crawl depth
            max_artifacts: Maximum artifacts to crawl (0 = unlimited)
            allowed_domains: List of allowed domains
            
        Returns:
            List of command arguments
        """
        # Use Python from ingestion service venv to run scrapy as module
        # This ensures we use the correct environment with all dependencies
        venv_python = self.ingestion_path / "venv" / "bin" / "python"
        if venv_python.exists():
            cmd = [str(venv_python), "-m", "scrapy", "crawl", spider_name]
        else:
            # Fallback to system scrapy if venv doesn't exist
            cmd = ["scrapy", "crawl", spider_name]
        
        cmd.extend([
            "-a", f"source_id={source_id}",
            "-a", f"job_id={job_id}",
            "-a", f"max_depth={max_depth}",
            "-a", f"max_artifacts={max_artifacts}",
        ])
        
        # Add start URLs as comma-separated string (Scrapy accepts this)
        if start_urls:
            start_urls_str = ",".join(start_urls)
            cmd.extend(["-a", f"start_urls={start_urls_str}"])
        
        # Add allowed domains if specified
        if allowed_domains:
            allowed_domains_str = ",".join(allowed_domains)
            cmd.extend(["-a", f"allowed_domains={allowed_domains_str}"])
        
        return cmd
    
    def _start_spider_process(self, scrapy_cmd: list) -> subprocess.Popen:
        """
        Start Scrapy spider process
        
        Args:
            scrapy_cmd: Scrapy command arguments (already fully formed from _build_scrapy_command)
            
        Returns:
            Popen process instance
            
        Raises:
            RuntimeError: If process cannot be started
        """
        try:
            logger.info(f"Starting spider with command: {' '.join(scrapy_cmd)}")
            
            # Prepare environment with MinIO credentials
            env = os.environ.copy()
            env['MINIO_ACCESS_KEY'] = settings.MINIO_ACCESS_KEY
            env['MINIO_SECRET_KEY'] = settings.MINIO_SECRET_KEY
            env['MINIO_ENDPOINT'] = settings.MINIO_ENDPOINT if settings.MINIO_ENDPOINT.startswith('http') else f'http://{settings.MINIO_ENDPOINT}'
            env['DATABASE_URL'] = settings.DATABASE_URL
            env['NORMALIZE_SERVICE_URL'] = f'http://{settings.TEMPORAL_HOST}:8001'  # Use detected IP
            env['LOREGUARD_HOST_IP'] = settings.TEMPORAL_HOST  # TEMPORAL_HOST has the detected IP
            
            logger.info(f"Environment: MINIO_ACCESS_KEY={env['MINIO_ACCESS_KEY']}, MINIO_ENDPOINT={env['MINIO_ENDPOINT']}")
            
            # Start the process (scrapy_cmd is already complete from _build_scrapy_command)
            process = subprocess.Popen(
                scrapy_cmd,
                cwd=str(self.ingestion_path),
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                env=env,  # Pass environment variables
                start_new_session=True  # Detach from parent process
            )
            
            logger.info(f"Spider process started with PID: {process.pid}")
            return process
            
        except FileNotFoundError as e:
            error_msg = (
                f"Scrapy command not found: {scrapy_cmd[0]}\n"
                f"Command attempted: {' '.join(scrapy_cmd)}\n\n"
                f"Ensure Scrapy is installed:\n"
                f"  cd {self.ingestion_path}\n"
                f"  venv/bin/pip install scrapy\n"
                f"Or run: bash scripts/dev/setup-ingestion-venv.sh"
            )
            logger.error(error_msg)
            raise RuntimeError(error_msg) from e
        except Exception as e:
            error_msg = f"Failed to start spider process: {type(e).__name__}: {e}"
            logger.error(error_msg)
            raise RuntimeError(error_msg) from e
    
    def get_crawl_status(self, job_id: str, db: Session) -> Dict[str, Any]:
        """
        Get status of a crawl job with comprehensive monitoring
        
        Args:
            job_id: Job ID
            db: Database session
            
        Returns:
            Dictionary with job status information including process monitoring
        """
        from services.job_monitoring_service import JobMonitoringService
        
        job = db.query(Job).filter(Job.id == job_id).first()
        
        if not job:
            raise ValueError(f"Job {job_id} not found")
        
        # Use monitoring service for comprehensive status
        monitoring_service = JobMonitoringService()
        return monitoring_service.check_job_status(job, db)

