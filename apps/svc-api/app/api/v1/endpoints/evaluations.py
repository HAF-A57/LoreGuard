"""
Evaluations API endpoints
"""

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import Optional
import uuid

from db.database import get_db
from models.evaluation import Evaluation

router = APIRouter()

@router.get("/")
async def list_evaluations(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    artifact_id: Optional[uuid.UUID] = Query(None),
    label: Optional[str] = Query(None),
    rubric_version: Optional[str] = Query(None),
    db: Session = Depends(get_db)
):
    """
    List evaluations with optional filtering
    """
    query = db.query(Evaluation)
    
    # Apply filters
    if artifact_id:
        query = query.filter(Evaluation.artifact_id == str(artifact_id))
    
    if label:
        query = query.filter(Evaluation.label == label)
    
    if rubric_version:
        query = query.filter(Evaluation.rubric_version == rubric_version)
    
    # Get total count
    total = query.count()
    
    # Apply pagination
    evaluations = query.order_by(Evaluation.created_at.desc()).offset(skip).limit(limit).all()
    
    return {
        "items": evaluations,
        "total": total,
        "skip": skip,
        "limit": limit
    }

@router.get("/{evaluation_id}")
async def get_evaluation(
    evaluation_id: uuid.UUID,
    db: Session = Depends(get_db)
):
    """
    Get specific evaluation by ID
    """
    evaluation = db.query(Evaluation).filter(Evaluation.id == str(evaluation_id)).first()
    
    if not evaluation:
        raise HTTPException(status_code=404, detail="Evaluation not found")
    
    return evaluation

