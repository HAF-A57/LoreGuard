"""
LLM Provider Pydantic schemas for request/response validation
"""

from pydantic import BaseModel, Field, validator
from typing import Optional, Dict, Any, List
from datetime import datetime
import uuid


class LLMProviderBase(BaseModel):
    """Base LLM provider schema"""
    name: str = Field(..., min_length=1, max_length=255, description="Provider display name")
    provider: str = Field(..., min_length=1, max_length=100, description="Provider type (openai, anthropic, etc.)")
    model: str = Field(..., min_length=1, max_length=100, description="Model identifier")
    base_url: Optional[str] = Field(None, max_length=500, description="Custom API base URL")
    status: str = Field(default="inactive", description="Provider status")
    priority: str = Field(default="normal", description="Priority level")
    config: Dict[str, Any] = Field(default_factory=dict, description="Provider-specific configuration")
    max_tokens: Optional[str] = Field(None, description="Max tokens per request")
    temperature: Optional[str] = Field(None, description="Default temperature")
    timeout: Optional[str] = Field(None, description="Request timeout")
    description: Optional[str] = Field(None, description="Provider description")
    is_default: bool = Field(default=False, description="Set as default provider")
    
    @validator("status")
    def validate_status(cls, v):
        allowed_statuses = ["active", "backup", "inactive"]
        if v not in allowed_statuses:
            raise ValueError(f"Status must be one of: {allowed_statuses}")
        return v
    
    @validator("priority")
    def validate_priority(cls, v):
        allowed_priorities = ["primary", "backup", "normal"]
        if v not in allowed_priorities:
            raise ValueError(f"Priority must be one of: {allowed_priorities}")
        return v
    
    @validator("provider")
    def validate_provider(cls, v):
        allowed_providers = ["openai", "anthropic", "azure", "local", "custom"]
        if v not in allowed_providers:
            raise ValueError(f"Provider must be one of: {allowed_providers}")
        return v


class LLMProviderCreate(LLMProviderBase):
    """Schema for creating new LLM provider"""
    api_key: str = Field(..., min_length=1, description="API key (will be encrypted)")


class LLMProviderUpdate(BaseModel):
    """Schema for updating LLM provider"""
    name: Optional[str] = Field(None, min_length=1, max_length=255)
    provider: Optional[str] = Field(None, min_length=1, max_length=100)
    model: Optional[str] = Field(None, min_length=1, max_length=100)
    api_key: Optional[str] = Field(None, min_length=1, description="API key (will be encrypted)")
    base_url: Optional[str] = Field(None, max_length=500)
    status: Optional[str] = None
    priority: Optional[str] = None
    config: Optional[Dict[str, Any]] = None
    max_tokens: Optional[str] = None
    temperature: Optional[str] = None
    timeout: Optional[str] = None
    description: Optional[str] = None
    is_default: Optional[bool] = None
    
    @validator("status")
    def validate_status(cls, v):
        if v is not None:
            allowed_statuses = ["active", "backup", "inactive"]
            if v not in allowed_statuses:
                raise ValueError(f"Status must be one of: {allowed_statuses}")
        return v


class LLMProviderResponse(LLMProviderBase):
    """LLM provider response schema"""
    id: uuid.UUID
    usage_count: str = Field(default="0")
    cost_per_token: Optional[str] = None
    avg_response_time: Optional[str] = None
    created_at: datetime
    updated_at: datetime
    api_key_masked: str = Field(..., description="Masked API key for display")
    
    class Config:
        from_attributes = True


class LLMProviderListItem(BaseModel):
    """Simplified provider for list responses"""
    id: uuid.UUID
    name: str
    provider: str
    model: str
    status: str
    priority: str
    is_default: bool
    usage_count: str
    created_at: datetime
    api_key_masked: str = Field(..., description="Masked API key for display")
    
    class Config:
        from_attributes = True


class LLMProviderListResponse(BaseModel):
    """Paginated provider list response"""
    items: List[LLMProviderListItem]
    total: int
    skip: int
    limit: int
    
    @property
    def has_next(self) -> bool:
        return self.skip + self.limit < self.total
    
    @property
    def has_prev(self) -> bool:
        return self.skip > 0

