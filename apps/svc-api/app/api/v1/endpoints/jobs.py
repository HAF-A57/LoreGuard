"""
Jobs API endpoints

Provides job monitoring, status tracking, and process management.
Includes real-time status updates, timeout detection, and kill switches.
"""

from fastapi import APIRouter, Depends, HTTPException, Query, Body
from sqlalchemy.orm import Session
from typing import Optional
import uuid
from pydantic import BaseModel

from db.database import get_db
from models.job import Job
from services.job_monitoring_service import JobMonitoringService

router = APIRouter()
monitoring_service = JobMonitoringService()


@router.get("/")
async def list_jobs(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    status: Optional[str] = Query(None),
    job_type: Optional[str] = Query(None),
    db: Session = Depends(get_db)
):
    """
    List jobs with optional filtering
    
    Args:
        skip: Number of records to skip
        limit: Maximum number of records to return
        status: Filter by job status (pending, running, completed, failed)
        job_type: Filter by job type (ingest, normalize, evaluate)
        
    Returns:
        Paginated list of jobs
    """
    query = db.query(Job)
    
    # Apply filters
    if status:
        query = query.filter(Job.status == status)
    
    if job_type:
        query = query.filter(Job.type == job_type)
    
    # Get total count
    total = query.count()
    
    # Apply pagination and ordering
    jobs = query.order_by(Job.created_at.desc()).offset(skip).limit(limit).all()
    
    return {
        "items": jobs,
        "total": total,
        "skip": skip,
        "limit": limit
    }


@router.get("/{job_id}")
async def get_job(
    job_id: uuid.UUID,
    include_process_info: bool = Query(True, description="Include real-time process information"),
    db: Session = Depends(get_db)
):
    """
    Get specific job by ID with real-time status
    
    Args:
        job_id: Job UUID
        include_process_info: Include real-time process monitoring data
        
    Returns:
        Job details with timeline, status, and process information
    """
    job = db.query(Job).filter(Job.id == str(job_id)).first()
    
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
    
    if include_process_info:
        # Get comprehensive status with process monitoring
        return monitoring_service.check_job_status(job, db)
    else:
        # Return basic job info
        return job


@router.post("/{job_id}/cancel")
async def cancel_job(
    job_id: uuid.UUID,
    force: bool = Body(False, description="Force kill process immediately"),
    db: Session = Depends(get_db)
):
    """
    Cancel/kill a running job
    
    Provides kill switch for users to terminate hanging or unwanted jobs.
    Supports both graceful termination and force kill.
    
    Args:
        job_id: Job UUID
        force: If True, force kill immediately (default: graceful termination)
        
    Returns:
        Cancellation result with process kill status
    """
    job = db.query(Job).filter(Job.id == str(job_id)).first()
    
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
    
    try:
        result = monitoring_service.cancel_job(job, db, force=force)
        return result
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except RuntimeError as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/{job_id}/retry")
async def retry_job(
    job_id: uuid.UUID,
    db: Session = Depends(get_db)
):
    """
    Retry a failed, cancelled, or timed-out job
    
    Creates a new job with the same configuration and increments retry count.
    
    Args:
        job_id: Job UUID to retry
        
    Returns:
        New job instance for retry
    """
    job = db.query(Job).filter(Job.id == str(job_id)).first()
    
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
    
    try:
        new_job = monitoring_service.retry_job(job, db)
        return {
            "message": "Retry job created",
            "original_job_id": str(job_id),
            "new_job_id": new_job.id,
            "retry_count": new_job.retries
        }
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/active/list")
async def list_active_jobs(db: Session = Depends(get_db)):
    """
    Get all active jobs with real-time status monitoring
    
    Returns running, pending, and hanging jobs with process information.
    Useful for dashboard displays and monitoring.
    
    Returns:
        List of active jobs with comprehensive status
    """
    active_jobs = monitoring_service.get_active_jobs(db)
    
    return {
        "active_jobs": active_jobs,
        "count": len(active_jobs)
    }


@router.get("/health/summary")
async def get_job_health_summary(db: Session = Depends(get_db)):
    """
    Get overall job system health summary
    
    Provides metrics for monitoring system health, detecting issues,
    and understanding job system performance.
    
    Returns:
        Health summary with job counts and status metrics
    """
    return monitoring_service.get_job_health_summary(db)

