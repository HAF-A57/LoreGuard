"""
Rubrics API endpoints
"""

from fastapi import APIRouter, Depends, HTTPException, Query, Body
from sqlalchemy.orm import Session
from typing import Optional, Dict, Any
import uuid

from db.database import get_db
from models.rubric import Rubric
from schemas.rubric import RubricCreate, RubricUpdate, RubricResponse, RubricListResponse, RubricListItem

router = APIRouter()


@router.get("/", response_model=RubricListResponse)
async def list_rubrics(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    is_active: Optional[bool] = Query(None),
    db: Session = Depends(get_db)
):
    """
    List all rubrics with optional filtering
    
    Args:
        skip: Number of records to skip
        limit: Maximum number of records to return
        is_active: Filter by active status
        
    Returns:
        Paginated list of rubrics
    """
    query = db.query(Rubric)
    
    # Apply filters
    if is_active is not None:
        query = query.filter(Rubric.is_active == is_active)
    
    # Get total count
    total = query.count()
    
    # Apply pagination and ordering
    rubrics = query.order_by(Rubric.created_at.desc()).offset(skip).limit(limit).all()
    
    items = []
    for r in rubrics:
        # Handle id conversion - Rubric.id is stored as String in DB
        rubric_id = r.id
        if isinstance(rubric_id, str):
            rubric_id = uuid.UUID(rubric_id)
        elif not isinstance(rubric_id, uuid.UUID):
            rubric_id = uuid.UUID(str(rubric_id))
        
        items.append(RubricListItem(
            id=rubric_id,
            version=r.version,
            is_active=r.is_active,
            created_at=r.created_at
        ))
    
    return RubricListResponse(
        items=items,
        total=total,
        skip=skip,
        limit=limit
    )


@router.get("/active")
async def get_active_rubric(db: Session = Depends(get_db)):
    """
    Get the currently active rubric
    
    Returns:
        Active rubric details
        
    Raises:
        HTTPException: If no active rubric is found
    """
    rubric = db.query(Rubric).filter(Rubric.is_active == True).first()
    
    if not rubric:
        raise HTTPException(
            status_code=404,
            detail="No active rubric found. Please activate a rubric first."
        )
    
    # Convert categories from array to dict format if needed (for compatibility with older rubrics)
    categories = rubric.categories
    if isinstance(categories, list):
        categories = {cat.get('id', f"category_{idx}"): {
            'weight': cat.get('weight', 0),
            'guidance': cat.get('description') or cat.get('guidance', ''),
            'subcriteria': cat.get('criteria') or cat.get('subcriteria', []),
            'scale': cat.get('scale', {'min': 0, 'max': 5})
        } for idx, cat in enumerate(categories)}
    
    # Create response directly using RubricResponse schema with converted categories
    return RubricResponse(
        id=uuid.UUID(rubric.id) if isinstance(rubric.id, str) else rubric.id,
        version=rubric.version,
        categories=categories,
        thresholds=rubric.thresholds,
        prompts=rubric.prompts,
        is_active=rubric.is_active,
        created_at=rubric.created_at
    )


@router.get("/{rubric_id}", response_model=RubricResponse)
async def get_rubric(
    rubric_id: uuid.UUID,
    db: Session = Depends(get_db)
):
    """
    Get specific rubric by ID
    
    Args:
        rubric_id: Rubric UUID
        
    Returns:
        Rubric details
    """
    rubric = db.query(Rubric).filter(Rubric.id == str(rubric_id)).first()
    
    if not rubric:
        raise HTTPException(status_code=404, detail="Rubric not found")
    
    # Convert categories from array to dict format if needed (for compatibility with older rubrics)
    categories = rubric.categories
    if isinstance(categories, list):
        categories = {cat.get('id', f"category_{idx}"): {
            'weight': cat.get('weight', 0),
            'guidance': cat.get('description') or cat.get('guidance', ''),
            'subcriteria': cat.get('criteria') or cat.get('subcriteria', []),
            'scale': cat.get('scale', {'min': 0, 'max': 5})
        } for idx, cat in enumerate(categories)}
    
    # Create response directly using RubricResponse schema with converted categories
    # This bypasses FastAPI's automatic serialization which would use the original array format
    return RubricResponse(
        id=uuid.UUID(rubric.id) if isinstance(rubric.id, str) else rubric.id,
        version=rubric.version,
        categories=categories,
        thresholds=rubric.thresholds,
        prompts=rubric.prompts,
        is_active=rubric.is_active,
        created_at=rubric.created_at
    )


@router.post("/", response_model=RubricResponse)
async def create_rubric(
    rubric: RubricCreate,
    db: Session = Depends(get_db)
):
    """
    Create a new rubric
    
    Args:
        rubric: Rubric creation data
        
    Returns:
        Created rubric details
    """
    # Check if version already exists
    existing = db.query(Rubric).filter(Rubric.version == rubric.version).first()
    if existing:
        raise HTTPException(
            status_code=400,
            detail=f"Rubric version '{rubric.version}' already exists"
        )
    
    # If setting as active, deactivate all others
    if rubric.is_active:
        db.query(Rubric).filter(Rubric.is_active == True).update({"is_active": False})
    
    # Create rubric
    db_rubric = Rubric(
        version=rubric.version,
        categories=rubric.categories,
        thresholds=rubric.thresholds,
        prompts=rubric.prompts,
        is_active=rubric.is_active
    )
    
    db.add(db_rubric)
    db.commit()
    db.refresh(db_rubric)
    
    return db_rubric


@router.put("/{rubric_id}", response_model=RubricResponse)
async def update_rubric(
    rubric_id: uuid.UUID,
    rubric_update: RubricUpdate,
    db: Session = Depends(get_db)
):
    """
    Update an existing rubric
    
    Args:
        rubric_id: Rubric UUID
        rubric_update: Rubric update data
        
    Returns:
        Updated rubric details
    """
    rubric = db.query(Rubric).filter(Rubric.id == str(rubric_id)).first()
    
    if not rubric:
        raise HTTPException(status_code=404, detail="Rubric not found")
    
    # If updating version, check for conflicts
    if rubric_update.version and rubric_update.version != rubric.version:
        existing = db.query(Rubric).filter(Rubric.version == rubric_update.version).first()
        if existing:
            raise HTTPException(
                status_code=400,
                detail=f"Rubric version '{rubric_update.version}' already exists"
            )
    
    # If setting as active, deactivate all others
    if rubric_update.is_active is True:
        db.query(Rubric).filter(Rubric.id != str(rubric_id)).update({"is_active": False})
    
    # Update fields
    update_data = rubric_update.dict(exclude_unset=True)
    for field, value in update_data.items():
        setattr(rubric, field, value)
    
    db.commit()
    db.refresh(rubric)
    
    return rubric


@router.put("/{rubric_id}/activate", response_model=RubricResponse)
async def activate_rubric(
    rubric_id: uuid.UUID,
    db: Session = Depends(get_db)
):
    """
    Activate a rubric (deactivates all others)
    
    Args:
        rubric_id: Rubric UUID to activate
        
    Returns:
        Activated rubric details
    """
    rubric = db.query(Rubric).filter(Rubric.id == str(rubric_id)).first()
    
    if not rubric:
        raise HTTPException(status_code=404, detail="Rubric not found")
    
    # Deactivate all other rubrics
    db.query(Rubric).filter(Rubric.id != str(rubric_id)).update({"is_active": False})
    
    # Activate this rubric
    rubric.is_active = True
    db.commit()
    db.refresh(rubric)
    
    return rubric


@router.delete("/{rubric_id}")
async def delete_rubric(
    rubric_id: uuid.UUID,
    db: Session = Depends(get_db)
):
    """
    Delete a rubric
    
    Args:
        rubric_id: Rubric UUID to delete
        
    Returns:
        Deletion confirmation
    """
    rubric = db.query(Rubric).filter(Rubric.id == str(rubric_id)).first()
    
    if not rubric:
        raise HTTPException(status_code=404, detail="Rubric not found")
    
    # Prevent deletion of active rubric
    if rubric.is_active:
        raise HTTPException(
            status_code=400,
            detail="Cannot delete active rubric. Activate another rubric first."
        )
    
    # Check if rubric has evaluations
    from models.evaluation import Evaluation
    evaluation_count = db.query(Evaluation).filter(
        Evaluation.rubric_version == rubric.version
    ).count()
    
    if evaluation_count > 0:
        raise HTTPException(
            status_code=400,
            detail=f"Cannot delete rubric with {evaluation_count} evaluations. Archive it instead (set is_active=False)."
        )
    
    db.delete(rubric)
    db.commit()
    
    return {"message": f"Rubric '{rubric.version}' deleted successfully"}

