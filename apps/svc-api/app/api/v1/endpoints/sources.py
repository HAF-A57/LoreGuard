"""
Sources API endpoints
"""

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from sqlalchemy import func
from typing import List, Optional
import uuid
import json

from db.database import get_db
from models.source import Source
from models.artifact import Artifact
from models.job import Job
from schemas.source import SourceResponse, SourceListResponse, SourceCreate, SourceUpdate
from services.crawl_service_subprocess import CrawlServiceSubprocess
from services.source_health import SourceHealthService

router = APIRouter()

def serialize_source(source: Source, doc_count: int = 0) -> dict:
    """Serialize source model to response format"""
    source_dict = {
        "id": uuid.UUID(source.id) if isinstance(source.id, str) else source.id,
        "name": source.name,
        "type": source.type,
        "config": source.config if isinstance(source.config, dict) else {},
        "schedule": source.schedule,
        "status": source.status,
        "tags": json.loads(source.tags) if source.tags else [],
        "last_run": source.last_run,
        "created_at": source.created_at,
        "updated_at": source.updated_at,
        "document_count": doc_count
    }
    return source_dict

@router.get("/", response_model=SourceListResponse)
async def list_sources(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    status: Optional[str] = Query(None),
    include_deleted: bool = Query(False, description="Include deleted sources"),
    db: Session = Depends(get_db)
):
    """
    List all data sources with optional filtering
    By default, excludes deleted sources unless include_deleted=True
    """
    query = db.query(Source)
    
    # Exclude deleted sources by default
    if not include_deleted:
        query = query.filter(Source.status != 'deleted')
    
    # Apply status filter (if provided, this overrides include_deleted)
    if status:
        query = query.filter(Source.status == status)
    
    # Get total count
    total = query.count()
    
    # Apply pagination and get results
    sources = query.offset(skip).limit(limit).all()
    
    # Add document counts for each source
    source_responses = []
    for source in sources:
        doc_count = db.query(func.count(Artifact.id)).filter(
            Artifact.source_id == source.id
        ).scalar()
        
        # SourceListItem only needs specific fields
        source_dict = {
            "id": uuid.UUID(source.id) if isinstance(source.id, str) else source.id,
            "name": source.name,
            "type": source.type,
            "status": source.status,
            "last_run": source.last_run,
            "document_count": doc_count,
            "created_at": source.created_at
        }
        source_responses.append(source_dict)
    
    return SourceListResponse(
        items=source_responses,
        total=total,
        skip=skip,
        limit=limit
    )

@router.get("/{source_id}", response_model=SourceResponse)
async def get_source(
    source_id: uuid.UUID,
    db: Session = Depends(get_db)
):
    """
    Get specific source by ID
    """
    # Convert UUID to string for database query (id is stored as VARCHAR)
    source = db.query(Source).filter(Source.id == str(source_id)).first()
    
    if not source:
        raise HTTPException(status_code=404, detail="Source not found")
    
    # Add document count
    doc_count = db.query(func.count(Artifact.id)).filter(
        Artifact.source_id == str(source_id)
    ).scalar()
    
    return serialize_source(source, doc_count)

@router.post("/", response_model=SourceResponse)
async def create_source(
    source: SourceCreate,
    db: Session = Depends(get_db)
):
    """
    Create new data source
    """
    source_data = source.dict()
    
    # Validate config has start_urls
    if not source_data.get('config', {}).get('start_urls'):
        raise HTTPException(
            status_code=400,
            detail="At least one start_url is required in config.start_urls"
        )
    
    # Convert tags list to JSON string for storage
    if source_data.get('tags'):
        source_data['tags'] = json.dumps(source_data['tags'])
    else:
        source_data['tags'] = None
    
    db_source = Source(**source_data)
    db.add(db_source)
    db.commit()
    db.refresh(db_source)
    
    return serialize_source(db_source, 0)

@router.put("/{source_id}", response_model=SourceResponse)
async def update_source(
    source_id: uuid.UUID,
    source_update: SourceUpdate,
    db: Session = Depends(get_db)
):
    """
    Update existing source
    """
    # Convert UUID to string for database query
    db_source = db.query(Source).filter(Source.id == str(source_id)).first()
    
    if not db_source:
        raise HTTPException(status_code=404, detail="Source not found")
    
    # Update fields
    update_data = source_update.dict(exclude_unset=True)
    
    # Convert tags list to JSON string if provided
    if 'tags' in update_data and update_data['tags'] is not None:
        update_data['tags'] = json.dumps(update_data['tags'])
    elif 'tags' in update_data and update_data['tags'] is None:
        update_data['tags'] = None
    
    for field, value in update_data.items():
        setattr(db_source, field, value)
    
    db.commit()
    db.refresh(db_source)
    
    # Add document count
    doc_count = db.query(func.count(Artifact.id)).filter(
        Artifact.source_id == str(source_id)
    ).scalar()
    
    return serialize_source(db_source, doc_count)

@router.delete("/{source_id}")
async def delete_source(
    source_id: uuid.UUID,
    db: Session = Depends(get_db)
):
    """
    Delete source (soft delete by setting status to 'deleted')
    """
    # Convert UUID to string for database query
    db_source = db.query(Source).filter(Source.id == str(source_id)).first()
    
    if not db_source:
        raise HTTPException(status_code=404, detail="Source not found")
    
    db_source.status = "deleted"
    db.commit()
    
    return {"message": "Source deleted successfully"}

@router.post("/{source_id}/trigger")
async def trigger_source_crawl(
    source_id: str,
    db: Session = Depends(get_db)
):
    """
    Trigger manual crawl for a source
    
    Validates source configuration and starts a Scrapy spider to crawl the source.
    Creates a job record to track the crawl progress.
    """
    source = db.query(Source).filter(Source.id == str(source_id)).first()
    
    if not source:
        raise HTTPException(status_code=404, detail="Source not found")
    
    if source.status != "active":
        raise HTTPException(
            status_code=400, 
            detail=f"Source is not active (current status: {source.status})"
        )
    
    # Initialize crawl service
    try:
        crawl_service = CrawlServiceSubprocess()
    except ValueError as e:
        raise HTTPException(
            status_code=500,
            detail=f"Crawl service initialization failed: {str(e)}"
        )
    
    # Trigger crawl
    try:
        import logging
        from datetime import datetime, timezone
        logger = logging.getLogger(__name__)
        logger.info(f"[ENDPOINT] About to call trigger_crawl for source {source.id}")
        job = crawl_service.trigger_crawl(source=source, db=db)
        logger.info(f"[ENDPOINT] trigger_crawl returned job {job.id}, status={job.status}")
        logger.info(f"[ENDPOINT] job.payload={job.payload}")
        
        # Update source last_run timestamp
        source.last_run = datetime.now(timezone.utc)
        db.commit()
        logger.info(f"[ENDPOINT] Updated last_run for source {source.id}")
        
        return {
            "message": "Crawl triggered successfully",
            "source_id": str(source_id),
            "source_name": source.name,
            "job_id": job.id,
            "status": job.status,
            "spider_name": job.payload.get("spider_name") if job.payload else None,
            "process_id": job.payload.get("process_id") if job.payload else None
        }
        
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except RuntimeError as e:
        raise HTTPException(status_code=500, detail=str(e))
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Unexpected error triggering crawl: {str(e)}"
        )

@router.get("/{source_id}/crawl-status")
async def get_source_crawl_status(
    source_id: uuid.UUID,
    db: Session = Depends(get_db)
):
    """
    Get the latest crawl job status for a source
    
    Returns the most recent ingest job for this source with real-time status,
    including progress, timeline, and process information.
    """
    from models.job import Job
    from services.job_monitoring_service import JobMonitoringService
    
    # First check if source exists and is not paused
    source = db.query(Source).filter(Source.id == str(source_id)).first()
    if not source:
        raise HTTPException(status_code=404, detail="Source not found")
    
    # Don't show crawl status for paused sources
    if source.status == "paused":
        return {
            "source_id": str(source_id),
            "has_active_crawl": False,
            "latest_job": None,
            "status": "source_paused"
        }
    
    # Get latest ingest job for this source
    # Query all ingest jobs and filter in Python (SQLAlchemy JSON querying can be tricky)
    source_id_str = str(source_id)
    ingest_jobs = (
        db.query(Job)
        .filter(Job.type == "ingest")
        .order_by(Job.created_at.desc())
        .all()
    )
    
    latest_job = None
    for job in ingest_jobs:
        if job.payload and job.payload.get("source_id") == source_id_str:
            latest_job = job
            break
    
    if not latest_job:
        return {
            "source_id": source_id_str,
            "has_active_crawl": False,
            "latest_job": None,
            "status": "no_jobs"
        }
    
    # Get comprehensive job status with monitoring (this will auto-update stale jobs)
    monitoring_service = JobMonitoringService()
    job_status = monitoring_service.check_job_status(latest_job, db)
    
    # Refresh job from DB in case status was updated
    db.refresh(latest_job)
    
    # Verify the job is actually active (check both DB status and process status)
    is_actually_running = False
    if latest_job.status in ["pending", "running"]:
        # Double-check process is actually running
        process_running = job_status.get("process_running", False)
        if latest_job.status == "running" and not process_running:
            # Process not running but job marked as running - not actually active
            is_actually_running = False
        else:
            is_actually_running = True
    
    return {
        "source_id": source_id_str,
        "has_active_crawl": is_actually_running,
        "latest_job": job_status,
        "status": latest_job.status
    }

@router.get("/{source_id}/health")
async def get_source_health(
    source_id: uuid.UUID,
    db: Session = Depends(get_db)
):
    """
    Get health metrics for a specific source
    """
    source = db.query(Source).filter(Source.id == str(source_id)).first()
    
    if not source:
        raise HTTPException(status_code=404, detail="Source not found")
    
    try:
        health_service = SourceHealthService()
        health_data = health_service.calculate_health(source, db)
        return health_data
    except Exception as e:
        import logging
        logger = logging.getLogger(__name__)
        logger.error(f"Error calculating health for source {source_id}: {e}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"Failed to calculate source health: {str(e)}"
        )

