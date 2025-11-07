"""
Artifacts API endpoints
"""

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import List, Optional
import uuid
import logging

from db.database import get_db
from models.artifact import Artifact, DocumentMetadata
from models.evaluation import Evaluation
from schemas.artifact import ArtifactResponse, ArtifactListResponse

router = APIRouter()
logger = logging.getLogger(__name__)

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
    provider_id: Optional[uuid.UUID] = None,
    db: Session = Depends(get_db)
):
    """
    Trigger evaluation for an artifact using configured LLM provider
    """
    from services.llm_evaluation import LLMEvaluationService
    
    artifact = db.query(Artifact).filter(Artifact.id == artifact_id).first()
    
    if not artifact:
        raise HTTPException(status_code=404, detail="Artifact not found")
    
    if not artifact.normalized_ref:
        raise HTTPException(
            status_code=400,
            detail="Artifact must be normalized before evaluation. Normalize the artifact first."
        )
    
    # Perform evaluation
    try:
        evaluation_service = LLMEvaluationService(db=db)
        evaluation = await evaluation_service.evaluate_artifact(
            artifact_id=str(artifact_id),
            rubric_version=rubric_version or "latest",
            provider_id=str(provider_id) if provider_id else None,
            db=db
        )
        
        return {
            "message": "Evaluation completed",
            "artifact_id": artifact_id,
            "evaluation_id": evaluation.id,
            "label": evaluation.label,
            "confidence": float(evaluation.confidence) if evaluation.confidence else 0.0,
            "total_score": evaluation.total_score,
            "scores": evaluation.scores,
            "model_used": evaluation.model_id,
            "rubric_version": evaluation.rubric_version
        }
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except RuntimeError as e:
        raise HTTPException(status_code=500, detail=str(e))
    except Exception as e:
        logger.error(f"Unexpected error during evaluation: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Evaluation failed: {str(e)}")

