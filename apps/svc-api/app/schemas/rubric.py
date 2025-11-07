"""
Rubric Pydantic schemas for request/response validation
"""

from pydantic import BaseModel, Field, validator
from typing import Dict, Any, Optional
from datetime import datetime
import uuid


class RubricBase(BaseModel):
    """Base rubric schema"""
    version: str = Field(..., min_length=1, max_length=50, description="Rubric version identifier")
    categories: Dict[str, Any] = Field(..., description="Scoring categories with weights and guidance")
    thresholds: Dict[str, Any] = Field(..., description="Score thresholds for Signal/Review/Noise")
    prompts: Dict[str, Any] = Field(..., description="LLM prompts for different evaluation stages")
    is_active: bool = Field(default=False, description="Set as active rubric (deactivates others)")
    
    @validator("categories")
    def validate_categories(cls, v):
        """Validate categories structure"""
        if not isinstance(v, dict):
            raise ValueError("Categories must be a dictionary")
        if len(v) == 0:
            raise ValueError("At least one category is required")
        
        total_weight = sum(cat.get('weight', 0) for cat in v.values() if isinstance(cat, dict))
        if abs(total_weight - 1.0) > 0.01:  # Allow small floating point differences
            raise ValueError(f"Category weights must sum to 1.0 (got {total_weight})")
        
        return v
    
    @validator("thresholds")
    def validate_thresholds(cls, v):
        """Validate thresholds structure"""
        if not isinstance(v, dict):
            raise ValueError("Thresholds must be a dictionary")
        
        required_keys = ['signal_min', 'review_min']
        for key in required_keys:
            if key not in v:
                raise ValueError(f"Missing required threshold: {key}")
        
        signal_min = v.get('signal_min', 0)
        review_min = v.get('review_min', 0)
        
        if signal_min < review_min:
            raise ValueError("signal_min must be >= review_min")
        
        return v


class RubricCreate(RubricBase):
    """Schema for creating new rubric"""
    pass


class RubricUpdate(BaseModel):
    """Schema for updating rubric"""
    version: Optional[str] = Field(None, min_length=1, max_length=50)
    categories: Optional[Dict[str, Any]] = None
    thresholds: Optional[Dict[str, Any]] = None
    prompts: Optional[Dict[str, Any]] = None
    is_active: Optional[bool] = None
    
    @validator("categories")
    def validate_categories(cls, v):
        """Validate categories if provided"""
        if v is not None:
            if not isinstance(v, dict):
                raise ValueError("Categories must be a dictionary")
            if len(v) == 0:
                raise ValueError("At least one category is required")
            
            total_weight = sum(cat.get('weight', 0) for cat in v.values() if isinstance(cat, dict))
            if abs(total_weight - 1.0) > 0.01:
                raise ValueError(f"Category weights must sum to 1.0 (got {total_weight})")
        
        return v
    
    @validator("thresholds")
    def validate_thresholds(cls, v):
        """Validate thresholds if provided"""
        if v is not None:
            if not isinstance(v, dict):
                raise ValueError("Thresholds must be a dictionary")
            
            signal_min = v.get('signal_min', 0)
            review_min = v.get('review_min', 0)
            
            if 'signal_min' in v and 'review_min' in v and signal_min < review_min:
                raise ValueError("signal_min must be >= review_min")
        
        return v


class RubricResponse(RubricBase):
    """Rubric response schema"""
    id: uuid.UUID
    created_at: datetime
    
    class Config:
        from_attributes = True


class RubricListItem(BaseModel):
    """Simplified rubric for list responses"""
    id: uuid.UUID
    version: str
    is_active: bool
    created_at: datetime
    
    class Config:
        from_attributes = True


class RubricListResponse(BaseModel):
    """Paginated rubric list response"""
    items: list[RubricListItem]
    total: int
    skip: int
    limit: int
    
    @property
    def has_next(self) -> bool:
        return self.skip + self.limit < self.total
    
    @property
    def has_prev(self) -> bool:
        return self.skip > 0

