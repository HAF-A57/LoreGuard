"""
Job Health Checker Background Task

Periodically checks job health, detects hanging jobs, and updates status.
Should be run as a background task or scheduled job.
"""

import logging
import asyncio
from datetime import datetime, timedelta, timezone
from typing import List
from sqlalchemy.orm import Session

from db.database import SessionLocal
from models.job import Job
from services.job_monitoring_service import JobMonitoringService

logger = logging.getLogger(__name__)


class JobHealthChecker:
    """Background service for monitoring job health"""
    
    def __init__(self, check_interval_seconds: int = 60):
        """
        Initialize job health checker
        
        Args:
            check_interval_seconds: How often to check job health (default: 60s)
        """
        self.check_interval = check_interval_seconds
        self.monitoring_service = JobMonitoringService()
        self.running = False
    
    async def start_monitoring(self):
        """Start background monitoring loop"""
        self.running = True
        logger.info("Starting job health checker background task")
        
        while self.running:
            try:
                await self.check_all_jobs()
                await asyncio.sleep(self.check_interval)
            except Exception as e:
                logger.error(f"Error in job health checker: {e}", exc_info=True)
                await asyncio.sleep(self.check_interval)
    
    def stop_monitoring(self):
        """Stop background monitoring"""
        self.running = False
        logger.info("Stopping job health checker")
    
    async def check_all_jobs(self):
        """Check all active jobs for health issues"""
        db = SessionLocal()
        
        try:
            # Get all running jobs
            running_jobs = db.query(Job).filter(
                Job.status.in_(["running", "pending"])
            ).all()
            
            logger.debug(f"Checking {len(running_jobs)} active jobs")
            
            for job in running_jobs:
                try:
                    # Check job status (this will auto-detect hanging jobs)
                    status_info = self.monitoring_service.check_job_status(job, db)
                    
                    # Log warnings for hanging jobs
                    if status_info.get("is_hanging"):
                        logger.warning(
                            f"Detected hanging job {job.id}: {status_info.get('hanging_reason')}"
                        )
                    
                except Exception as e:
                    logger.error(f"Error checking job {job.id}: {e}")
            
            # Clean up stale jobs (jobs that have been running too long without updates)
            await self._cleanup_stale_jobs(db)
            
        finally:
            db.close()
    
    async def _cleanup_stale_jobs(self, db: Session):
        """Clean up jobs that appear to be stale/dead"""
        # Find jobs that have been running for more than 2 hours without updates
        stale_threshold = datetime.now(timezone.utc) - timedelta(hours=2)
        
        stale_jobs = db.query(Job).filter(
            Job.status == "running",
            Job.updated_at < stale_threshold
        ).all()
        
        for job in stale_jobs:
            # Check if process is actually running
            process_id = job.payload.get("process_id") if job.payload else None
            
            if process_id:
                try:
                    import psutil
                    process = psutil.Process(process_id)
                    # Process exists, but job hasn't been updated - mark as hanging
                    if not process.is_running():
                        logger.warning(f"Marking stale job {job.id} as failed (process dead)")
                        job.status = "failed"
                        job.error = "Job process died without updating status"
                        job.add_timeline_entry("failed", "Process died without status update")
                        db.commit()
                except psutil.NoSuchProcess:
                    # Process doesn't exist - mark as failed
                    logger.warning(f"Marking stale job {job.id} as failed (process not found)")
                    job.status = "failed"
                    job.error = "Job process not found"
                    job.add_timeline_entry("failed", "Process not found")
                    db.commit()
                except Exception as e:
                    logger.error(f"Error checking stale job {job.id}: {e}")

