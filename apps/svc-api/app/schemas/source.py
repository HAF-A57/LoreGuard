"""
Source Pydantic schemas for request/response validation
"""

from pydantic import BaseModel, Field, validator
from typing import List, Optional, Dict, Any
from datetime import datetime
import uuid

class SourceBase(BaseModel):
    """Base source schema"""
    name: str = Field(..., min_length=1, max_length=255)
    type: str = Field(..., min_length=1, max_length=50)
    config: Dict[str, Any] = Field(default_factory=dict)
    schedule: Optional[str] = None
    status: str = Field(default="active")
    tags: Optional[List[str]] = None
    
    @validator("status")
    def validate_status(cls, v):
        allowed_statuses = ["active", "paused", "error", "deleted"]
        if v not in allowed_statuses:
            raise ValueError(f"Status must be one of: {allowed_statuses}")
        return v
    
    @validator("type")
    def validate_type(cls, v):
        allowed_types = ["web", "api", "feed", "rss", "twitter", "reddit", "news"]
        if v not in allowed_types:
            raise ValueError(f"Type must be one of: {allowed_types}")
        return v

class SourceCreate(SourceBase):
    """Schema for creating new sources"""
    pass

class SourceUpdate(BaseModel):
    """Schema for updating sources"""
    name: Optional[str] = Field(None, min_length=1, max_length=255)
    type: Optional[str] = Field(None, min_length=1, max_length=50)
    config: Optional[Dict[str, Any]] = None
    schedule: Optional[str] = None
    status: Optional[str] = None
    tags: Optional[List[str]] = None
    
    @validator("status")
    def validate_status(cls, v):
        if v is not None:
            allowed_statuses = ["active", "paused", "error", "deleted"]
            if v not in allowed_statuses:
                raise ValueError(f"Status must be one of: {allowed_statuses}")
        return v
    
    @validator("type")
    def validate_type(cls, v):
        if v is not None:
            allowed_types = ["web", "api", "feed", "rss", "twitter", "reddit", "news"]
            if v not in allowed_types:
                raise ValueError(f"Type must be one of: {allowed_types}")
        return v

class SourceResponse(SourceBase):
    """Source response schema"""
    id: uuid.UUID
    last_run: Optional[datetime] = None
    document_count: int = Field(default=0)
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True

class SourceListItem(BaseModel):
    """Simplified source for list responses"""
    id: uuid.UUID
    name: str
    type: str
    status: str
    last_run: Optional[datetime] = None
    document_count: int = Field(default=0)
    created_at: datetime
    
    class Config:
        from_attributes = True

class SourceListResponse(BaseModel):
    """Paginated source list response"""
    items: List[SourceListItem]
    total: int
    skip: int
    limit: int
    
    @property
    def has_next(self) -> bool:
        return self.skip + self.limit < self.total
    
    @property
    def has_prev(self) -> bool:
        return self.skip > 0

