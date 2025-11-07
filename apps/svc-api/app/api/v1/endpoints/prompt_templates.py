"""
Prompt Templates API endpoints
"""

from fastapi import APIRouter, Depends, HTTPException, Query, Body
from sqlalchemy.orm import Session
from typing import Optional, List
import uuid

from db.database import get_db
from models.prompt_template import PromptTemplate
from schemas.prompt_template import (
    PromptTemplateCreate,
    PromptTemplateUpdate,
    PromptTemplateResponse,
    PromptTemplateListResponse,
    PromptTemplateListItem
)

router = APIRouter()


@router.get("/", response_model=PromptTemplateListResponse)
async def list_prompt_templates(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    type: Optional[str] = Query(None, description="Filter by prompt type"),
    is_active: Optional[bool] = Query(None, description="Filter by active status"),
    is_default: Optional[bool] = Query(None, description="Filter by default status"),
    db: Session = Depends(get_db)
):
    """
    List all prompt templates with optional filtering
    
    Args:
        skip: Number of records to skip
        limit: Maximum number of records to return
        type: Filter by prompt type (metadata, evaluation, clarification)
        is_active: Filter by active status
        is_default: Filter by default status
        
    Returns:
        Paginated list of prompt templates
    """
    query = db.query(PromptTemplate)
    
    # Apply filters
    if type:
        query = query.filter(PromptTemplate.type == type)
    if is_active is not None:
        query = query.filter(PromptTemplate.is_active == is_active)
    if is_default is not None:
        query = query.filter(PromptTemplate.is_default == is_default)
    
    # Get total count
    total = query.count()
    
    # Apply pagination and ordering
    templates = query.order_by(PromptTemplate.created_at.desc()).offset(skip).limit(limit).all()
    
    items = []
    for t in templates:
        template_id = t.id
        if isinstance(template_id, str):
            template_id = uuid.UUID(template_id)
        elif not isinstance(template_id, uuid.UUID):
            template_id = uuid.UUID(str(template_id))
        
        items.append(PromptTemplateListItem(
            id=template_id,
            reference_id=t.reference_id,
            name=t.name,
            type=t.type,
            version=t.version,
            description=t.description,
            is_active=t.is_active,
            is_default=t.is_default,
            usage_count=int(t.usage_count) if t.usage_count else 0,
            created_at=t.created_at
        ))
    
    return PromptTemplateListResponse(
        items=items,
        total=total,
        skip=skip,
        limit=limit
    )


@router.get("/{template_id}", response_model=PromptTemplateResponse)
async def get_prompt_template(
    template_id: uuid.UUID,
    db: Session = Depends(get_db)
):
    """
    Get specific prompt template by ID
    
    Args:
        template_id: Template UUID
        
    Returns:
        Prompt template details
    """
    template = db.query(PromptTemplate).filter(PromptTemplate.id == str(template_id)).first()
    
    if not template:
        raise HTTPException(status_code=404, detail="Prompt template not found")
    
    template_id_uuid = uuid.UUID(template.id) if isinstance(template.id, str) else template.id
    
    return PromptTemplateResponse(
        id=template_id_uuid,
        reference_id=template.reference_id,
        name=template.name,
        type=template.type,
        version=template.version,
        system_prompt=template.system_prompt,
        user_prompt_template=template.user_prompt_template,
        description=template.description,
        variables=template.variables or {},
        config=template.config or {},
        is_active=template.is_active,
        is_default=template.is_default,
        tags=template.tags or [],
        usage_count=int(template.usage_count) if template.usage_count else 0,
        created_at=template.created_at,
        updated_at=template.updated_at,
        created_by=template.created_by
    )


@router.get("/reference/{reference_id}", response_model=PromptTemplateResponse)
async def get_prompt_template_by_reference(
    reference_id: str,
    db: Session = Depends(get_db)
):
    """
    Get prompt template by reference ID
    
    Args:
        reference_id: Template reference ID (e.g., 'prompt_ref_meta_v2_1')
        
    Returns:
        Prompt template details
    """
    template = db.query(PromptTemplate).filter(PromptTemplate.reference_id == reference_id).first()
    
    if not template:
        raise HTTPException(status_code=404, detail=f"Prompt template with reference '{reference_id}' not found")
    
    template_id_uuid = uuid.UUID(template.id) if isinstance(template.id, str) else template.id
    
    return PromptTemplateResponse(
        id=template_id_uuid,
        reference_id=template.reference_id,
        name=template.name,
        type=template.type,
        version=template.version,
        system_prompt=template.system_prompt,
        user_prompt_template=template.user_prompt_template,
        description=template.description,
        variables=template.variables or {},
        config=template.config or {},
        is_active=template.is_active,
        is_default=template.is_default,
        tags=template.tags or [],
        usage_count=int(template.usage_count) if template.usage_count else 0,
        created_at=template.created_at,
        updated_at=template.updated_at,
        created_by=template.created_by
    )


@router.get("/type/{prompt_type}/default", response_model=PromptTemplateResponse)
async def get_default_prompt_template(
    prompt_type: str,
    db: Session = Depends(get_db)
):
    """
    Get the default prompt template for a specific type
    
    Args:
        prompt_type: Prompt type (metadata, evaluation, clarification)
        
    Returns:
        Default prompt template for the type
    """
    template = db.query(PromptTemplate).filter(
        PromptTemplate.type == prompt_type,
        PromptTemplate.is_default == True,
        PromptTemplate.is_active == True
    ).first()
    
    if not template:
        raise HTTPException(
            status_code=404,
            detail=f"No default active prompt template found for type '{prompt_type}'"
        )
    
    template_id_uuid = uuid.UUID(template.id) if isinstance(template.id, str) else template.id
    
    return PromptTemplateResponse(
        id=template_id_uuid,
        reference_id=template.reference_id,
        name=template.name,
        type=template.type,
        version=template.version,
        system_prompt=template.system_prompt,
        user_prompt_template=template.user_prompt_template,
        description=template.description,
        variables=template.variables or {},
        config=template.config or {},
        is_active=template.is_active,
        is_default=template.is_default,
        tags=template.tags or [],
        usage_count=int(template.usage_count) if template.usage_count else 0,
        created_at=template.created_at,
        updated_at=template.updated_at,
        created_by=template.created_by
    )


@router.post("/", response_model=PromptTemplateResponse, status_code=201)
async def create_prompt_template(
    template: PromptTemplateCreate,
    db: Session = Depends(get_db)
):
    """
    Create a new prompt template
    
    Args:
        template: Prompt template data
        
    Returns:
        Created prompt template
    """
    # Check if reference_id already exists
    existing = db.query(PromptTemplate).filter(PromptTemplate.reference_id == template.reference_id).first()
    if existing:
        raise HTTPException(
            status_code=400,
            detail=f"Prompt template with reference '{template.reference_id}' already exists"
        )
    
    # If setting as default, unset other defaults of the same type
    if template.is_default:
        db.query(PromptTemplate).filter(
            PromptTemplate.type == template.type,
            PromptTemplate.is_default == True
        ).update({"is_default": False})
    
    # Create new template
    new_template = PromptTemplate(
        reference_id=template.reference_id,
        name=template.name,
        type=template.type,
        version=template.version,
        system_prompt=template.system_prompt,
        user_prompt_template=template.user_prompt_template,
        description=template.description,
        variables=template.variables or {},
        config=template.config or {},
        is_active=template.is_active,
        is_default=template.is_default,
        tags=template.tags or [],
        created_by=template.created_by
    )
    
    db.add(new_template)
    db.commit()
    db.refresh(new_template)
    
    template_id_uuid = uuid.UUID(new_template.id) if isinstance(new_template.id, str) else new_template.id
    
    return PromptTemplateResponse(
        id=template_id_uuid,
        reference_id=new_template.reference_id,
        name=new_template.name,
        type=new_template.type,
        version=new_template.version,
        system_prompt=new_template.system_prompt,
        user_prompt_template=new_template.user_prompt_template,
        description=new_template.description,
        variables=new_template.variables or {},
        config=new_template.config or {},
        is_active=new_template.is_active,
        is_default=new_template.is_default,
        tags=new_template.tags or [],
        usage_count=int(new_template.usage_count) if new_template.usage_count else 0,
        created_at=new_template.created_at,
        updated_at=new_template.updated_at,
        created_by=new_template.created_by
    )


@router.put("/{template_id}", response_model=PromptTemplateResponse)
async def update_prompt_template(
    template_id: uuid.UUID,
    template_update: PromptTemplateUpdate,
    db: Session = Depends(get_db)
):
    """
    Update a prompt template
    
    Args:
        template_id: Template UUID
        template_update: Updated template data
        
    Returns:
        Updated prompt template
    """
    template = db.query(PromptTemplate).filter(PromptTemplate.id == str(template_id)).first()
    
    if not template:
        raise HTTPException(status_code=404, detail="Prompt template not found")
    
    # If setting as default, unset other defaults of the same type
    if template_update.is_default is True and template.is_default is False:
        db.query(PromptTemplate).filter(
            PromptTemplate.type == template.type,
            PromptTemplate.is_default == True,
            PromptTemplate.id != str(template_id)
        ).update({"is_default": False})
    
    # Update fields
    update_data = template_update.dict(exclude_unset=True)
    for field, value in update_data.items():
        setattr(template, field, value)
    
    db.commit()
    db.refresh(template)
    
    template_id_uuid = uuid.UUID(template.id) if isinstance(template.id, str) else template.id
    
    return PromptTemplateResponse(
        id=template_id_uuid,
        reference_id=template.reference_id,
        name=template.name,
        type=template.type,
        version=template.version,
        system_prompt=template.system_prompt,
        user_prompt_template=template.user_prompt_template,
        description=template.description,
        variables=template.variables or {},
        config=template.config or {},
        is_active=template.is_active,
        is_default=template.is_default,
        tags=template.tags or [],
        usage_count=int(template.usage_count) if template.usage_count else 0,
        created_at=template.created_at,
        updated_at=template.updated_at,
        created_by=template.created_by
    )


@router.delete("/{template_id}", status_code=204)
async def delete_prompt_template(
    template_id: uuid.UUID,
    db: Session = Depends(get_db)
):
    """
    Delete a prompt template
    
    Args:
        template_id: Template UUID
    """
    template = db.query(PromptTemplate).filter(PromptTemplate.id == str(template_id)).first()
    
    if not template:
        raise HTTPException(status_code=404, detail="Prompt template not found")
    
    # Prevent deletion of default templates
    if template.is_default:
        raise HTTPException(
            status_code=400,
            detail="Cannot delete default template. Set another template as default first."
        )
    
    db.delete(template)
    db.commit()
    
    return None

