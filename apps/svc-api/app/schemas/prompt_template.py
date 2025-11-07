"""
Prompt Template Pydantic schemas for request/response validation
"""

from pydantic import BaseModel, Field, validator
from typing import Dict, Any, Optional, List
from datetime import datetime
import uuid


class PromptTemplateBase(BaseModel):
    """Base prompt template schema"""
    reference_id: str = Field(..., min_length=1, max_length=255, description="Unique reference identifier (e.g., 'prompt_ref_meta_v2_1')")
    name: str = Field(..., min_length=1, max_length=255, description="Human-readable name")
    type: str = Field(..., description="Prompt type: metadata, evaluation, or clarification")
    version: str = Field(..., min_length=1, max_length=50, description="Version string (e.g., 'v2.1')")
    system_prompt: Optional[str] = Field(None, description="System prompt content (if applicable)")
    user_prompt_template: str = Field(..., min_length=1, description="User prompt template with placeholders")
    description: Optional[str] = Field(None, description="Description of what this prompt does")
    variables: Optional[Dict[str, Any]] = Field(default_factory=dict, description="Available variables for template substitution")
    config: Optional[Dict[str, Any]] = Field(default_factory=dict, description="Additional configuration")
    is_active: bool = Field(default=True, description="Whether this template is active")
    is_default: bool = Field(default=False, description="Default template for this type")
    tags: Optional[List[str]] = Field(default_factory=list, description="Tags for categorization")
    created_by: Optional[str] = Field(None, description="User who created this template")
    
    @validator("type")
    def validate_type(cls, v):
        """Validate prompt type"""
        allowed_types = ["metadata", "evaluation", "clarification"]
        if v not in allowed_types:
            raise ValueError(f"Type must be one of: {', '.join(allowed_types)}")
        return v
    
    @validator("reference_id")
    def validate_reference_id(cls, v):
        """Validate reference ID format"""
        if not v.startswith("prompt_ref_"):
            raise ValueError("Reference ID must start with 'prompt_ref_'")
        return v


class PromptTemplateCreate(PromptTemplateBase):
    """Schema for creating a new prompt template"""
    pass


class PromptTemplateUpdate(BaseModel):
    """Schema for updating a prompt template"""
    name: Optional[str] = Field(None, min_length=1, max_length=255)
    system_prompt: Optional[str] = None
    user_prompt_template: Optional[str] = Field(None, min_length=1)
    description: Optional[str] = None
    variables: Optional[Dict[str, Any]] = None
    config: Optional[Dict[str, Any]] = None
    is_active: Optional[bool] = None
    is_default: Optional[bool] = None
    tags: Optional[List[str]] = None
    version: Optional[str] = Field(None, min_length=1, max_length=50)


class PromptTemplateResponse(PromptTemplateBase):
    """Schema for prompt template response"""
    id: uuid.UUID
    usage_count: int = Field(default=0, description="Number of times this template has been used")
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True


class PromptTemplateListItem(BaseModel):
    """Schema for prompt template list item"""
    id: uuid.UUID
    reference_id: str
    name: str
    type: str
    version: str
    description: Optional[str]
    is_active: bool
    is_default: bool
    usage_count: int
    created_at: datetime
    
    class Config:
        from_attributes = True


class PromptTemplateListResponse(BaseModel):
    """Schema for paginated prompt template list"""
    items: List[PromptTemplateListItem]
    total: int
    skip: int
    limit: int

