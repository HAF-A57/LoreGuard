"""
Subprocess-Based Crawl Service for LoreGuard

Uses subprocess to execute docker exec directly, avoiding Docker SDK compatibility issues.
Provides comprehensive logging for troubleshooting.
"""

import os
import subprocess
import logging
import json
import shlex
from typing import Optional
from sqlalchemy.orm import Session

from models.source import Source
from models.job import Job
from core.config import settings

logger = logging.getLogger(__name__)


class CrawlServiceSubprocess:
    """Service for triggering web crawls using subprocess docker exec"""
    
    SPIDER_MAP = {
        "web": "generic_web",
        "api": "api_spider",
        "feed": "feed_spider"
    }
    
    INGESTION_CONTAINER_NAME = "loreguard-ingestion"
    
    def __init__(self):
        """Initialize subprocess-based crawl service"""
        logger.info("[CRAWL_SERVICE] Initializing subprocess-based crawl service...")
        
        # Verify docker command is available
        try:
            result = subprocess.run(
                ["docker", "ps", "-f", f"name={self.INGESTION_CONTAINER_NAME}", "--format", "{{.Names}}"],
                capture_output=True,
                text=True,
                timeout=5
            )
            
            if self.INGESTION_CONTAINER_NAME in result.stdout:
                logger.info(f"[CRAWL_SERVICE] Found ingestion container: {self.INGESTION_CONTAINER_NAME}")
            else:
                raise ValueError(f"Ingestion container '{self.INGESTION_CONTAINER_NAME}' not found")
                
        except subprocess.TimeoutExpired:
            raise ValueError("Docker command timed out")
        except FileNotFoundError:
            raise ValueError("Docker command not found")
        except Exception as e:
            raise ValueError(f"Failed to verify ingestion container: {e}")
    
    def trigger_crawl(
        self,
        source: Source,
        db: Session,
        job_id: Optional[str] = None
    ) -> Job:
        """
        Trigger a crawl by executing scrapy via docker exec
        """
        logger.info(f"[CRAWL_SERVICE] ===== TRIGGER CRAWL STARTED =====")
        logger.info(f"[CRAWL_SERVICE] Source ID: {source.id}")
        logger.info(f"[CRAWL_SERVICE] Source Name: {source.name}")
        
        # Validate
        self._validate_source_config(source)
        
        # Get spider name
        spider_name = self.SPIDER_MAP.get(source.type, "generic_web")
        logger.info(f"[CRAWL_SERVICE] Spider: {spider_name}")
        
        # Extract configuration
        config = source.config or {}
        crawl_config = config.get("crawl_scope", {})
        filtering_config = config.get("filtering", {})
        
        start_urls = config.get("start_urls", [])
        if not start_urls:
            raise ValueError(f"Source {source.id} has no start_urls")
        
        max_artifacts = crawl_config.get("max_artifacts", 0)
        max_depth = crawl_config.get("max_depth", 3)
        allowed_domains = filtering_config.get("allowed_domains", [])
        
        logger.info(f"[CRAWL_SERVICE] Start URLs: {start_urls}")
        logger.info(f"[CRAWL_SERVICE] Max artifacts: {max_artifacts}, Max depth: {max_depth}")
        
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
        
        # Pass full config as JSON for spider to access extraction settings
        config_json = json.dumps(config)
        
        # Build scrapy command arguments list
        scrapy_args = [
            "scrapy", "crawl", spider_name,
            "-a", f"source_id={source.id}",
            "-a", f"job_id={job.id}",
            "-a", f"max_depth={max_depth}",
            "-a", f"max_artifacts={max_artifacts}",
            "-a", f"start_urls={','.join(start_urls)}",
            "-a", f"allowed_domains={','.join(allowed_domains)}",
            "-a", f"config={shlex.quote(config_json)}"
        ]
        
        # Build docker exec command - run in background with output logging
        log_file = f"/app/logs/crawl_{job.id}.log"
        
        # Build command string that redirects output
        # Properly quote each argument for shell safety
        scrapy_cmd_parts = [shlex.quote(arg) for arg in scrapy_args]
        scrapy_cmd_str = " ".join(scrapy_cmd_parts)
        bash_cmd = f"cd /app && {scrapy_cmd_str} > {log_file} 2>&1"
        
        docker_cmd = [
            "docker", "exec",
            "-e", "MINIO_ENDPOINT=http://minio:9000",
            "-e", f"MINIO_ACCESS_KEY={os.getenv('MINIO_ACCESS_KEY', 'loreguard')}",
            "-e", f"MINIO_SECRET_KEY={os.getenv('MINIO_SECRET_KEY', 'minio_password_here')}",
            "-e", f"DATABASE_URL={os.getenv('DATABASE_URL', '')}",
            "-e", "NORMALIZE_SERVICE_URL=http://loreguard-normalize:8001",
            "-d",  # Detach mode
            self.INGESTION_CONTAINER_NAME,
            "bash", "-c", bash_cmd
        ]
        
        logger.info(f"[CRAWL_SERVICE] Executing: docker exec -d {self.INGESTION_CONTAINER_NAME} bash -c '{bash_cmd}'")
        logger.info(f"[CRAWL_SERVICE] Output will be logged to: {log_file}")
        
        # Execute command
        try:
            process = subprocess.Popen(
                docker_cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True
            )
            
            # Wait briefly for command to start
            try:
                process.wait(timeout=2)
                logger.info(f"[CRAWL_SERVICE] Docker exec started successfully")
            except subprocess.TimeoutExpired:
                # Command still running, which is expected for detached mode
                logger.info(f"[CRAWL_SERVICE] Docker exec detached (running in background)")
            
            # Update job
            job.status = "running"
            job.add_timeline_entry("running", f"Spider '{spider_name}' started")
            job.payload["log_file"] = log_file
            job.payload["container_name"] = self.INGESTION_CONTAINER_NAME
            db.commit()
            db.refresh(job)
            
            logger.info(f"[CRAWL_SERVICE] ===== CRAWL TRIGGERED SUCCESSFULLY =====")
            logger.info(f"[CRAWL_SERVICE] Job ID: {job.id}")
            logger.info(f"[CRAWL_SERVICE] Status: {job.status}")
            logger.info(f"[CRAWL_SERVICE] PID: {process.pid}")
            
            return job
            
        except Exception as e:
            error_msg = f"Failed to start spider: {e}"
            logger.error(f"[CRAWL_SERVICE] {error_msg}", exc_info=True)
            job.status = "failed"
            job.error = error_msg
            job.add_timeline_entry("failed", error_msg)
            db.commit()
            raise RuntimeError(error_msg)
    
    def _validate_source_config(self, source: Source):
        """Validate source configuration"""
        if not source.config:
            raise ValueError(f"Source {source.id} has no configuration")
        if "start_urls" not in source.config or not source.config["start_urls"]:
            raise ValueError(f"Source {source.id} has no start_urls")

