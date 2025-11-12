"""
Docker-Aware Crawl Service for LoreGuard

Handles web crawling by executing Scrapy in the ingestion container.
Provides comprehensive logging for troubleshooting.
"""

import os
import logging
import json
from typing import Optional
from pathlib import Path
from sqlalchemy.orm import Session
import docker
from docker.errors import DockerException, NotFound, APIError

from models.source import Source
from models.job import Job
from core.config import settings

logger = logging.getLogger(__name__)


class CrawlServiceDocker:
    """Service for triggering web crawls using Docker"""
    
    SPIDER_MAP = {
        "web": "generic_web",
        "api": "api_spider",
        "feed": "feed_spider"
    }
    
    INGESTION_CONTAINER_NAME = "loreguard-ingestion"
    
    def __init__(self):
        """Initialize Docker-aware crawl service"""
        logger.info("[CRAWL_SERVICE] Initializing Docker-aware crawl service...")
        
        try:
            # Use explicit unix socket to avoid http+docker URL scheme issues
            self.docker_client = docker.DockerClient(base_url='unix://var/run/docker.sock')
            logger.info("[CRAWL_SERVICE] Docker client initialized successfully")
            
            # Verify ingestion container exists
            try:
                container = self.docker_client.containers.get(self.INGESTION_CONTAINER_NAME)
                logger.info(f"[CRAWL_SERVICE] Found ingestion container: {container.name} (status: {container.status})")
            except NotFound:
                logger.error(f"[CRAWL_SERVICE] Ingestion container '{self.INGESTION_CONTAINER_NAME}' not found!")
                raise ValueError(f"Ingestion container '{self.INGESTION_CONTAINER_NAME}' not found. Ensure docker-compose is running.")
                
        except DockerException as e:
            logger.error(f"[CRAWL_SERVICE] Failed to initialize Docker client: {e}")
            raise ValueError(f"Docker is not available: {e}")
    
    def trigger_crawl(
        self,
        source: Source,
        db: Session,
        job_id: Optional[str] = None
    ) -> Job:
        """
        Trigger a crawl for a source by executing Scrapy in the ingestion container
        
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
        logger.info(f"[CRAWL_SERVICE] ===== TRIGGER CRAWL STARTED =====")
        logger.info(f"[CRAWL_SERVICE] Source ID: {source.id}")
        logger.info(f"[CRAWL_SERVICE] Source Name: {source.name}")
        logger.info(f"[CRAWL_SERVICE] Source Type: {source.type}")
        
        # Validate source configuration
        self._validate_source_config(source)
        
        # Determine spider name
        spider_name = self.SPIDER_MAP.get(source.type, "generic_web")
        logger.info(f"[CRAWL_SERVICE] Spider: {spider_name}")
        
        # Extract configuration
        config = source.config or {}
        crawl_config = config.get("crawl_scope", {})
        filtering_config = config.get("filtering", {})
        
        start_urls = config.get("start_urls", [])
        if not start_urls:
            raise ValueError(f"Source {source.id} has no start_urls configured")
        
        max_artifacts = crawl_config.get("max_artifacts", 0)
        max_depth = crawl_config.get("max_depth", 3)
        allowed_domains = filtering_config.get("allowed_domains", [])
        
        logger.info(f"[CRAWL_SERVICE] Configuration:")
        logger.info(f"[CRAWL_SERVICE]   Start URLs: {start_urls}")
        logger.info(f"[CRAWL_SERVICE]   Max artifacts: {max_artifacts}")
        logger.info(f"[CRAWL_SERVICE]   Max depth: {max_depth}")
        logger.info(f"[CRAWL_SERVICE]   Allowed domains: {allowed_domains}")
        
        # Create job
        if job_id:
            job = db.query(Job).filter(Job.id == job_id).first()
            if not job:
                raise ValueError(f"Job {job_id} not found")
        else:
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
            job.add_timeline_entry("pending", "Crawl job created")
            db.add(job)
            db.commit()
            db.refresh(job)
            logger.info(f"[CRAWL_SERVICE] Job created: {job.id}")
        
        # Build Scrapy command
        scrapy_args = [
            "scrapy", "crawl", spider_name,
            "-a", f"source_id={source.id}",
            "-a", f"job_id={job.id}",
            "-a", f"max_depth={max_depth}",
            "-a", f"max_artifacts={max_artifacts}",
            "-a", f"start_urls={','.join(start_urls)}",
            "-a", f"allowed_domains={','.join(allowed_domains)}"
        ]
        
        logger.info(f"[CRAWL_SERVICE] Scrapy command: {' '.join(scrapy_args)}")
        
        # Execute in Docker container
        try:
            logger.info(f"[CRAWL_SERVICE] Executing scrapy in container '{self.INGESTION_CONTAINER_NAME}'...")
            
            container = self.docker_client.containers.get(self.INGESTION_CONTAINER_NAME)
            
            # Prepare environment variables
            env_vars = {
                "MINIO_ENDPOINT": "http://minio:9000",  # Add http:// prefix
                "MINIO_ACCESS_KEY": os.getenv("MINIO_ACCESS_KEY", "loreguard"),
                "MINIO_SECRET_KEY": os.getenv("MINIO_SECRET_KEY", "minio_password_here"),
                "DATABASE_URL": os.getenv("DATABASE_URL", ""),
                "NORMALIZE_SERVICE_URL": "http://loreguard-normalize:8001",
            }
            
            logger.info(f"[CRAWL_SERVICE] Environment variables:")
            for key, value in env_vars.items():
                if "SECRET" in key or "PASSWORD" in key:
                    logger.info(f"[CRAWL_SERVICE]   {key}=***REDACTED***")
                else:
                    logger.info(f"[CRAWL_SERVICE]   {key}={value}")
            
            # Build environment string for docker exec
            env_string = " ".join([f'{k}="{v}"' for k, v in env_vars.items()])
            full_command = f"bash -c '{env_string} {' '.join(scrapy_args)}'"
            
            # Execute command
            logger.info(f"[CRAWL_SERVICE] Executing: {full_command}")
            
            exec_result = container.exec_run(
                cmd=full_command,
                environment=env_vars,
                detach=True,  # Run in background
                workdir="/app"
            )
            
            logger.info(f"[CRAWL_SERVICE] Exec result: {exec_result}")
            
            # Update job status
            job.status = "running"
            job.add_timeline_entry("running", f"Spider '{spider_name}' started in container")
            job.payload["container_name"] = self.INGESTION_CONTAINER_NAME
            job.payload["exec_id"] = exec_result.output.decode() if hasattr(exec_result.output, 'decode') else str(exec_result.output)
            db.commit()
            db.refresh(job)
            
            logger.info(f"[CRAWL_SERVICE] ===== CRAWL TRIGGERED SUCCESSFULLY =====")
            logger.info(f"[CRAWL_SERVICE] Job ID: {job.id}")
            logger.info(f"[CRAWL_SERVICE] Status: {job.status}")
            
            return job
            
        except NotFound as e:
            error_msg = f"Container '{self.INGESTION_CONTAINER_NAME}' not found: {e}"
            logger.error(f"[CRAWL_SERVICE] {error_msg}")
            job.status = "failed"
            job.error = error_msg
            job.add_timeline_entry("failed", error_msg)
            db.commit()
            raise RuntimeError(error_msg)
            
        except APIError as e:
            error_msg = f"Docker API error: {e}"
            logger.error(f"[CRAWL_SERVICE] {error_msg}")
            job.status = "failed"
            job.error = error_msg
            job.add_timeline_entry("failed", error_msg)
            db.commit()
            raise RuntimeError(error_msg)
            
        except Exception as e:
            error_msg = f"Unexpected error starting spider: {e}"
            logger.error(f"[CRAWL_SERVICE] {error_msg}", exc_info=True)
            job.status = "failed"
            job.error = error_msg
            job.add_timeline_entry("failed", error_msg)
            db.commit()
            raise RuntimeError(error_msg)
    
    def _validate_source_config(self, source: Source):
        """Validate source configuration"""
        logger.info(f"[CRAWL_SERVICE] Validating source configuration...")
        
        if not source.config:
            raise ValueError(f"Source {source.id} has no configuration")
        
        if "start_urls" not in source.config or not source.config["start_urls"]:
            raise ValueError(f"Source {source.id} has no start_urls")
        
        logger.info(f"[CRAWL_SERVICE] Source configuration is valid")
    
    def get_job_status(self, job_id: str, db: Session) -> dict:
        """Get detailed job status"""
        job = db.query(Job).filter(Job.id == job_id).first()
        if not job:
            return {"error": "Job not found"}
        
        return {
            "id": job.id,
            "type": job.type,
            "status": job.status,
            "timeline": job.timeline,
            "payload": job.payload,
            "error": job.error,
            "created_at": job.created_at.isoformat() if job.created_at else None
        }

