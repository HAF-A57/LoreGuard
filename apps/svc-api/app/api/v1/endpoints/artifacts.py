"""
Artifacts API endpoints
"""

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import List, Optional
import uuid

from db.database import get_db
from models.artifact import Artifact, DocumentMetadata
from models.evaluation import Evaluation
from schemas.artifact import ArtifactResponse, ArtifactListResponse

router = APIRouter()

@router.get("/", response_model=ArtifactListResponse)
async def list_artifacts(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    search: Optional[str] = Query(None),
    label: Optional[str] = Query(None),
    source_id: Optional[uuid.UUID] = Query(None),
    db: Session = Depends(get_db)
):
    """
    List artifacts with optional filtering and search
    """
    query = db.query(Artifact).join(DocumentMetadata, isouter=True)
    
    # Apply filters
    if search:
        query = query.filter(DocumentMetadata.title.ilike(f"%{search}%"))
    
    if source_id:
        query = query.filter(Artifact.source_id == source_id)
    
    if label:
        # Filter by latest evaluation label
        subquery = db.query(Evaluation.artifact_id).filter(
            Evaluation.label == label
        ).subquery()
        query = query.filter(Artifact.id.in_(subquery))
    
    # Get total count
    total = query.count()
    
    # Apply pagination
    artifacts = query.offset(skip).limit(limit).all()
    
    return ArtifactListResponse(
        items=artifacts,
        total=total,
        skip=skip,
        limit=limit
    )

@router.get("/{artifact_id}", response_model=ArtifactResponse)
async def get_artifact(
    artifact_id: uuid.UUID,
    db: Session = Depends(get_db)
):
    """
    Get specific artifact by ID
    """
    artifact = db.query(Artifact).filter(Artifact.id == artifact_id).first()
    
    if not artifact:
        raise HTTPException(status_code=404, detail="Artifact not found")
    
    return artifact

@router.get("/{artifact_id}/evaluations")
async def get_artifact_evaluations(
    artifact_id: uuid.UUID,
    db: Session = Depends(get_db)
):
    """
    Get all evaluations for an artifact
    """
    artifact = db.query(Artifact).filter(Artifact.id == artifact_id).first()
    
    if not artifact:
        raise HTTPException(status_code=404, detail="Artifact not found")
    
    evaluations = db.query(Evaluation).filter(
        Evaluation.artifact_id == artifact_id
    ).order_by(Evaluation.created_at.desc()).all()
    
    return {
        "artifact_id": artifact_id,
        "evaluations": evaluations
    }

@router.post("/{artifact_id}/evaluate")
async def trigger_evaluation(
    artifact_id: uuid.UUID,
    rubric_version: Optional[str] = None,
    db: Session = Depends(get_db)
):
    """
    Trigger evaluation for an artifact
    """
    artifact = db.query(Artifact).filter(Artifact.id == artifact_id).first()
    
    if not artifact:
        raise HTTPException(status_code=404, detail="Artifact not found")
    
    # TODO: Implement evaluation triggering via Temporal workflow
    # For now, return a placeholder response
    
    return {
        "message": "Evaluation triggered",
        "artifact_id": artifact_id,
        "rubric_version": rubric_version or "latest"
    }

