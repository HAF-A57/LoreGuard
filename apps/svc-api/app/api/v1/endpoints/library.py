"""
Library API endpoints

Library contains curated Signal artifacts - high-value documents
that have been evaluated and marked as Signal by the LLM evaluation system.
"""

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from sqlalchemy import func, desc
from typing import Optional
import uuid
import json

from db.database import get_db
from models.artifact import Artifact
from models.evaluation import Evaluation
from models.library import LibraryItem
from schemas.artifact import ArtifactListResponse, ArtifactListItem

router = APIRouter()


@router.get("/", response_model=ArtifactListResponse)
async def list_library_items(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    is_signal: Optional[bool] = Query(True, description="Filter by Signal status"),
    db: Session = Depends(get_db)
):
    """
    List library items (curated Signal artifacts)
    
    Returns artifacts that have been evaluated and labeled as Signal,
    or manually curated library items.
    
    Args:
        skip: Number of records to skip
        limit: Maximum number of records to return
        is_signal: Filter by Signal status (default: True)
        
    Returns:
        Paginated list of Signal artifacts
    """
    # Get Signal artifacts via latest evaluation
    # Join with evaluations to get only artifacts with Signal label
    # Use subquery to get latest evaluation per artifact
    from sqlalchemy import desc
    
    # Simpler approach: Get all evaluations with Signal label
    # Then filter to unique artifacts (latest evaluation)
    signal_evals = (
        db.query(Evaluation)
        .filter(Evaluation.label == "Signal")
        .order_by(Evaluation.artifact_id, Evaluation.created_at.desc())
        .all()
    )
    
    # Get unique artifact IDs
    seen_artifacts = set()
    signal_artifact_ids = []
    for ev in signal_evals:
        if ev.artifact_id not in seen_artifacts:
            seen_artifacts.add(ev.artifact_id)
            signal_artifact_ids.append(ev.artifact_id)
    
    # Query artifacts with Signal evaluations
    if signal_artifact_ids:
        query = db.query(Artifact).filter(Artifact.id.in_(signal_artifact_ids))
        
        # Get total count
        total = query.count()
        
        # Apply pagination and ordering (by artifact created_at since we don't have Evaluation in query)
        artifacts = query.order_by(desc(Artifact.created_at)).offset(skip).limit(limit).all()
    else:
        # No Signal artifacts found
        total = 0
        artifacts = []
    
    # Convert to response format
    items = []
    for artifact in artifacts:
        # Get latest evaluation
        latest_eval = (
            db.query(Evaluation)
            .filter(Evaluation.artifact_id == artifact.id)
            .order_by(Evaluation.created_at.desc())
            .first()
        )
        
        # Get metadata
        metadata = artifact.document_metadata
        
        item = ArtifactListItem(
            id=uuid.UUID(artifact.id),
            source_id=uuid.UUID(artifact.source_id),
            uri=artifact.uri,
            created_at=artifact.created_at,
            title=metadata.title if metadata else None,
            authors=(
                json.loads(metadata.authors) if metadata and metadata.authors 
                else None
            ),
            organization=metadata.organization if metadata else None,
            topics=(
                json.loads(metadata.topics) if metadata and metadata.topics 
                else None
            ),
            label=latest_eval.label if latest_eval else None,
            confidence=(
                float(latest_eval.confidence) 
                if latest_eval and latest_eval.confidence 
                else None
            )
        )
        items.append(item)
    
    return ArtifactListResponse(
        items=items,
        total=total,
        skip=skip,
        limit=limit
    )


@router.get("/{library_item_id}")
async def get_library_item(
    library_item_id: uuid.UUID,
    db: Session = Depends(get_db)
):
    """
    Get specific library item by ID
    
    Args:
        library_item_id: Library item UUID
        
    Returns:
        Library item details with artifact and evaluation info
    """
    library_item = db.query(LibraryItem).filter(
        LibraryItem.id == str(library_item_id)
    ).first()
    
    if not library_item:
        raise HTTPException(status_code=404, detail="Library item not found")
    
    # Get artifact and latest evaluation
    artifact = library_item.artifact
    latest_eval = (
        db.query(Evaluation)
        .filter(Evaluation.artifact_id == artifact.id)
        .order_by(Evaluation.created_at.desc())
        .first()
    )
    
    return {
        "id": library_item.id,
        "artifact_id": library_item.artifact_id,
        "is_signal": library_item.is_signal,
        "tags": json.loads(library_item.tags) if library_item.tags else [],
        "created_at": library_item.created_at,
        "artifact": artifact,
        "latest_evaluation": latest_eval
    }

