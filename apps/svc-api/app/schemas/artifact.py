"""
Artifact Pydantic schemas for request/response validation
"""

from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any
from datetime import datetime
import uuid

class MetadataBase(BaseModel):
    """Base metadata schema"""
    title: Optional[str] = None
    authors: Optional[List[str]] = None
    organization: Optional[str] = None
    pub_date: Optional[datetime] = None
    topics: Optional[List[str]] = None
    geo_location: Optional[str] = None
    language: Optional[str] = None

class MetadataResponse(MetadataBase):
    """Metadata response schema"""
    id: uuid.UUID
    artifact_id: uuid.UUID
    created_at: datetime
    
    class Config:
        from_attributes = True

class ClarificationResponse(BaseModel):
    """Clarification response schema"""
    id: uuid.UUID
    artifact_id: uuid.UUID
    signals: Dict[str, Any]
    evidence_ref: Optional[str] = None
    created_at: datetime
    
    class Config:
        from_attributes = True

class EvaluationSummary(BaseModel):
    """Summary evaluation info for artifact listings"""
    id: uuid.UUID
    rubric_version: str
    label: Optional[str] = None
    confidence: Optional[float] = None
    total_score: Optional[float] = None
    created_at: datetime

class ArtifactBase(BaseModel):
    """Base artifact schema"""
    uri: str
    content_hash: str
    mime_type: Optional[str] = None

class ArtifactResponse(ArtifactBase):
    """Artifact response schema"""
    id: uuid.UUID
    source_id: uuid.UUID
    version: int
    normalized_ref: Optional[str] = None
    created_at: datetime
    
    # Related data
    metadata: Optional[MetadataResponse] = None
    clarification: Optional[ClarificationResponse] = None
    latest_evaluation: Optional[EvaluationSummary] = None
    
    class Config:
        from_attributes = True

class ArtifactListItem(BaseModel):
    """Simplified artifact for list responses"""
    id: uuid.UUID
    source_id: uuid.UUID
    uri: str
    created_at: datetime
    
    # Metadata summary
    title: Optional[str] = None
    authors: Optional[List[str]] = None
    organization: Optional[str] = None
    topics: Optional[List[str]] = None
    
    # Latest evaluation summary
    label: Optional[str] = None
    confidence: Optional[float] = None
    
    class Config:
        from_attributes = True

class ArtifactListResponse(BaseModel):
    """Paginated artifact list response"""
    items: List[ArtifactListItem]
    total: int
    skip: int
    limit: int
    
    @property
    def has_next(self) -> bool:
        return self.skip + self.limit < self.total
    
    @property
    def has_prev(self) -> bool:
        return self.skip > 0

