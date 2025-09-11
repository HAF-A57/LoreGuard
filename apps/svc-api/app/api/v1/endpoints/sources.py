"""
Sources API endpoints
"""

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from sqlalchemy import func
from typing import List, Optional
import uuid

from db.database import get_db
from models.source import Source
from models.artifact import Artifact
from schemas.source import SourceResponse, SourceListResponse, SourceCreate, SourceUpdate

router = APIRouter()

@router.get("/", response_model=SourceListResponse)
async def list_sources(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    status: Optional[str] = Query(None),
    db: Session = Depends(get_db)
):
    """
    List all data sources with optional filtering
    """
    query = db.query(Source)
    
    # Apply status filter
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
        
        source_dict = {
            **source.__dict__,
            "document_count": doc_count
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
    source = db.query(Source).filter(Source.id == source_id).first()
    
    if not source:
        raise HTTPException(status_code=404, detail="Source not found")
    
    # Add document count
    doc_count = db.query(func.count(Artifact.id)).filter(
        Artifact.source_id == source_id
    ).scalar()
    
    source_dict = {
        **source.__dict__,
        "document_count": doc_count
    }
    
    return source_dict

@router.post("/", response_model=SourceResponse)
async def create_source(
    source: SourceCreate,
    db: Session = Depends(get_db)
):
    """
    Create new data source
    """
    db_source = Source(**source.dict())
    db.add(db_source)
    db.commit()
    db.refresh(db_source)
    
    return {**db_source.__dict__, "document_count": 0}

@router.put("/{source_id}", response_model=SourceResponse)
async def update_source(
    source_id: uuid.UUID,
    source_update: SourceUpdate,
    db: Session = Depends(get_db)
):
    """
    Update existing source
    """
    db_source = db.query(Source).filter(Source.id == source_id).first()
    
    if not db_source:
        raise HTTPException(status_code=404, detail="Source not found")
    
    # Update fields
    update_data = source_update.dict(exclude_unset=True)
    for field, value in update_data.items():
        setattr(db_source, field, value)
    
    db.commit()
    db.refresh(db_source)
    
    # Add document count
    doc_count = db.query(func.count(Artifact.id)).filter(
        Artifact.source_id == source_id
    ).scalar()
    
    return {**db_source.__dict__, "document_count": doc_count}

@router.delete("/{source_id}")
async def delete_source(
    source_id: uuid.UUID,
    db: Session = Depends(get_db)
):
    """
    Delete source (soft delete by setting status to 'deleted')
    """
    db_source = db.query(Source).filter(Source.id == source_id).first()
    
    if not db_source:
        raise HTTPException(status_code=404, detail="Source not found")
    
    db_source.status = "deleted"
    db.commit()
    
    return {"message": "Source deleted successfully"}

@router.post("/{source_id}/trigger")
async def trigger_source_crawl(
    source_id: uuid.UUID,
    db: Session = Depends(get_db)
):
    """
    Trigger manual crawl for a source
    """
    source = db.query(Source).filter(Source.id == source_id).first()
    
    if not source:
        raise HTTPException(status_code=404, detail="Source not found")
    
    if source.status != "active":
        raise HTTPException(status_code=400, detail="Source is not active")
    
    # TODO: Implement crawl triggering via Temporal workflow
    # For now, return a placeholder response
    
    return {
        "message": "Crawl triggered",
        "source_id": source_id,
        "source_name": source.name
    }

