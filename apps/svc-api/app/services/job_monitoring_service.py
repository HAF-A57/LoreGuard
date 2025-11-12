"""
Job Monitoring Service

Provides real-time job status monitoring, timeout detection, and process management.
Handles hanging jobs, error detection, and provides kill switches for user control.
"""

import os
import signal
import logging
import psutil
from typing import Dict, Any, Optional, List
from datetime import datetime, timedelta, timezone
from sqlalchemy.orm import Session

from models.job import Job
from core.config import settings

logger = logging.getLogger(__name__)


class JobMonitoringService:
    """Service for monitoring and managing job execution"""
    
    # Job timeout thresholds (in seconds)
    JOB_TIMEOUTS = {
        "ingest": 3600,  # 1 hour for ingestion jobs
        "normalize": 600,  # 10 minutes for normalization
        "evaluate": 300,  # 5 minutes for evaluation
        "export": 1800,  # 30 minutes for exports
        "default": 1800  # 30 minutes default
    }
    
    # Status definitions
    STATUS_PENDING = "pending"
    STATUS_RUNNING = "running"
    STATUS_COMPLETED = "completed"
    STATUS_FAILED = "failed"
    STATUS_CANCELLED = "cancelled"
    STATUS_TIMEOUT = "timeout"
    STATUS_HANGING = "hanging"
    
    def __init__(self):
        """Initialize job monitoring service"""
        self.monitoring_enabled = True
    
    def check_job_status(
        self,
        job: Job,
        db: Session
    ) -> Dict[str, Any]:
        """
        Check and update job status with real-time process information
        
        Args:
            job: Job model instance
            db: Database session
            
        Returns:
            Dictionary with comprehensive job status
        """
        status_info = {
            "id": job.id,  # Use 'id' for consistency with API responses
            "job_id": job.id,  # Keep 'job_id' for backward compatibility
            "type": job.type,
            "status": job.status,
            "created_at": job.created_at.isoformat() if job.created_at else None,
            "updated_at": job.updated_at.isoformat() if job.updated_at else None,
            "timeline": job.timeline or [],
            "error": job.error,
            "retries": job.retries,
        }
        
        # Get process information if available
        process_id = job.payload.get("process_id") if job.payload else None
        
        if process_id:
            process_info = self._get_process_info(process_id)
            status_info.update(process_info)
            
            # Check for hanging/timeout conditions
            if job.status == self.STATUS_RUNNING:
                hanging_check = self._check_hanging_job(job, process_info)
                if hanging_check["is_hanging"]:
                    status_info["is_hanging"] = True
                    status_info["hanging_reason"] = hanging_check["reason"]
                    
                    # Auto-update job status if hanging
                    if self.monitoring_enabled:
                        self._handle_hanging_job(job, hanging_check, db)
                else:
                    status_info["is_hanging"] = False
        else:
            status_info["process_running"] = False
            status_info["process_info"] = None
        
        # Calculate duration
        if job.created_at:
            duration = (datetime.now(timezone.utc) - job.created_at).total_seconds()
            status_info["duration_seconds"] = duration
            status_info["duration_formatted"] = self._format_duration(duration)
        
        # Get progress estimate if available
        if job.payload:
            status_info["progress"] = job.payload.get("progress", 0)
            status_info["items_processed"] = job.payload.get("items_processed", 0)
            status_info["total_items"] = job.payload.get("total_items", 0)
        
        return status_info
    
    def _get_process_info(self, process_id: int) -> Dict[str, Any]:
        """
        Get detailed information about a process
        
        Args:
            process_id: Process ID (PID)
            
        Returns:
            Dictionary with process information
        """
        try:
            process = psutil.Process(process_id)
            
            # Get process status
            status = process.status()
            
            # Get resource usage
            cpu_percent = process.cpu_percent(interval=0.1)
            memory_info = process.memory_info()
            memory_mb = memory_info.rss / (1024 * 1024)
            
            # Get runtime
            create_time = datetime.fromtimestamp(process.create_time())
            runtime = (datetime.now() - create_time).total_seconds()
            
            return {
                "process_running": True,
                "process_id": process_id,
                "process_status": status,
                "cpu_percent": cpu_percent,
                "memory_mb": round(memory_mb, 2),
                "runtime_seconds": runtime,
                "num_threads": process.num_threads(),
                "num_fds": process.num_fds() if hasattr(process, 'num_fds') else None,
            }
            
        except psutil.NoSuchProcess:
            return {
                "process_running": False,
                "process_id": process_id,
                "error": "Process not found"
            }
        except psutil.AccessDenied:
            return {
                "process_running": True,  # Assume running if we can't check
                "process_id": process_id,
                "error": "Access denied to process"
            }
        except Exception as e:
            logger.warning(f"Error getting process info for PID {process_id}: {e}")
            return {
                "process_running": None,
                "process_id": process_id,
                "error": str(e)
            }
    
    def _check_hanging_job(
        self,
        job: Job,
        process_info: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Check if a job is hanging or has timed out
        
        Args:
            job: Job model instance
            process_info: Process information dictionary
            
        Returns:
            Dictionary with hanging status and reason
        """
        # Check if process is still running
        if not process_info.get("process_running"):
            return {
                "is_hanging": False,
                "reason": None
            }
        
        # Get timeout threshold for job type
        timeout_seconds = self.JOB_TIMEOUTS.get(job.type, self.JOB_TIMEOUTS["default"])
        
        # Check if job has exceeded timeout
        if job.created_at:
            runtime = (datetime.now(timezone.utc) - job.created_at).total_seconds()
            if runtime > timeout_seconds:
                return {
                    "is_hanging": True,
                    "reason": f"Job exceeded timeout of {timeout_seconds}s (runtime: {runtime:.0f}s)",
                    "timeout_seconds": timeout_seconds,
                    "runtime_seconds": runtime
                }
        
        # Check if process is consuming resources but not progressing
        # (CPU usage, memory, but no timeline updates)
        if process_info.get("cpu_percent", 0) < 1.0:
            # Process is idle - check last timeline update
            if job.timeline:
                last_update = job.timeline[-1].get("timestamp")
                if last_update:
                    try:
                        last_update_time = datetime.fromisoformat(last_update.replace('Z', '+00:00'))
                        idle_time = (datetime.utcnow() - last_update_time.replace(tzinfo=None)).total_seconds()
                        
                        # If idle for more than 5 minutes and job type should be active
                        if idle_time > 300 and job.type in ["ingest", "normalize", "evaluate"]:
                            return {
                                "is_hanging": True,
                                "reason": f"Job appears idle (no updates for {idle_time:.0f}s)",
                                "idle_seconds": idle_time
                            }
                    except Exception:
                        pass
        
        return {
            "is_hanging": False,
            "reason": None
        }
    
    def _handle_hanging_job(
        self,
        job: Job,
        hanging_info: Dict[str, Any],
        db: Session
    ):
        """
        Handle a detected hanging job
        
        Args:
            job: Job model instance
            hanging_info: Hanging detection information
            db: Database session
        """
        logger.warning(
            f"Detected hanging job {job.id}: {hanging_info['reason']}"
        )
        
        # Update job status
        job.status = self.STATUS_HANGING
        job.error = f"Hanging job detected: {hanging_info['reason']}"
        job.add_timeline_entry(
            self.STATUS_HANGING,
            hanging_info['reason']
        )
        
        db.commit()
    
    def cancel_job(
        self,
        job: Job,
        db: Session,
        force: bool = False
    ) -> Dict[str, Any]:
        """
        Cancel/kill a running job
        
        Args:
            job: Job model instance
            db: Database session
            force: If True, force kill the process immediately
            
        Returns:
            Dictionary with cancellation result
        """
        if job.status not in [self.STATUS_RUNNING, self.STATUS_HANGING, self.STATUS_PENDING]:
            raise ValueError(f"Cannot cancel job in status: {job.status}")
        
        process_id = job.payload.get("process_id") if job.payload else None
        
        kill_result = {
            "job_id": job.id,
            "cancelled": False,
            "process_killed": False,
            "message": ""
        }
        
        if process_id:
            try:
                process = psutil.Process(process_id)
                
                if force:
                    # Force kill immediately
                    process.kill()
                    kill_result["process_killed"] = True
                    kill_result["message"] = f"Process {process_id} force killed"
                else:
                    # Graceful termination
                    process.terminate()
                    
                    # Wait up to 5 seconds for graceful shutdown
                    try:
                        process.wait(timeout=5)
                        kill_result["process_killed"] = True
                        kill_result["message"] = f"Process {process_id} terminated gracefully"
                    except psutil.TimeoutExpired:
                        # Force kill if graceful shutdown failed
                        process.kill()
                        kill_result["process_killed"] = True
                        kill_result["message"] = f"Process {process_id} force killed after timeout"
                
                logger.info(f"Cancelled job {job.id}, killed process {process_id}")
                
            except psutil.NoSuchProcess:
                kill_result["message"] = f"Process {process_id} not found (may have already completed)"
            except psutil.AccessDenied:
                kill_result["message"] = f"Access denied to process {process_id}"
                raise RuntimeError(f"Cannot kill process {process_id}: Access denied")
            except Exception as e:
                logger.error(f"Error killing process {process_id}: {e}")
                raise RuntimeError(f"Failed to kill process: {e}")
        else:
            kill_result["message"] = "No process ID associated with job"
        
        # Update job status
        job.status = self.STATUS_CANCELLED
        job.add_timeline_entry(
            self.STATUS_CANCELLED,
            kill_result["message"]
        )
        db.commit()
        
        kill_result["cancelled"] = True
        return kill_result
    
    def retry_job(
        self,
        job: Job,
        db: Session
    ) -> Job:
        """
        Retry a failed or cancelled job
        
        Args:
            job: Job model instance
            db: Database session
            
        Returns:
            New job instance for retry
        """
        if job.status not in [self.STATUS_FAILED, self.STATUS_CANCELLED, self.STATUS_TIMEOUT]:
            raise ValueError(f"Cannot retry job in status: {job.status}")
        
        # Create new job with same configuration
        new_job = Job(
            type=job.type,
            status=self.STATUS_PENDING,
            payload=job.payload.copy() if job.payload else {},
            retries=job.retries + 1
        )
        new_job.add_timeline_entry(
            self.STATUS_PENDING,
            f"Retry attempt {new_job.retries} for job {job.id}"
        )
        
        db.add(new_job)
        db.commit()
        
        logger.info(f"Created retry job {new_job.id} for failed job {job.id}")
        
        return new_job
    
    def get_active_jobs(self, db: Session) -> List[Dict[str, Any]]:
        """
        Get all active (running/pending) jobs with real-time status
        
        Args:
            db: Database session
            
        Returns:
            List of active job status dictionaries
        """
        active_jobs = db.query(Job).filter(
            Job.status.in_([self.STATUS_RUNNING, self.STATUS_PENDING, self.STATUS_HANGING])
        ).all()
        
        return [self.check_job_status(job, db) for job in active_jobs]
    
    def get_job_health_summary(self, db: Session) -> Dict[str, Any]:
        """
        Get overall job system health summary
        
        Args:
            db: Database session
            
        Returns:
            Dictionary with health metrics
        """
        total_jobs = db.query(Job).count()
        running_jobs = db.query(Job).filter(Job.status == self.STATUS_RUNNING).count()
        pending_jobs = db.query(Job).filter(Job.status == self.STATUS_PENDING).count()
        failed_jobs = db.query(Job).filter(Job.status == self.STATUS_FAILED).count()
        hanging_jobs = db.query(Job).filter(Job.status == self.STATUS_HANGING).count()
        completed_jobs = db.query(Job).filter(Job.status == self.STATUS_COMPLETED).count()
        
        # Get recent failures (last 24 hours)
        recent_failures = db.query(Job).filter(
            Job.status == self.STATUS_FAILED,
            Job.created_at >= datetime.utcnow() - timedelta(days=1)
        ).count()
        
        return {
            "total_jobs": total_jobs,
            "running_jobs": running_jobs,
            "pending_jobs": pending_jobs,
            "failed_jobs": failed_jobs,
            "hanging_jobs": hanging_jobs,
            "completed_jobs": completed_jobs,
            "recent_failures_24h": recent_failures,
            "health_status": "healthy" if hanging_jobs == 0 and failed_jobs < 10 else "degraded"
        }
    
    def _format_duration(self, seconds: float) -> str:
        """Format duration in human-readable format"""
        if seconds < 60:
            return f"{seconds:.0f}s"
        elif seconds < 3600:
            minutes = seconds / 60
            return f"{minutes:.1f}m"
        else:
            hours = seconds / 3600
            return f"{hours:.1f}h"

