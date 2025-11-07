"""
Prompt Template model for managing LLM prompt templates
"""

from sqlalchemy import Column, String, DateTime, Text, Boolean, JSON
from sqlalchemy.sql import func
import uuid

from db.database import Base


class PromptTemplate(Base):
    """
    Prompt Template model for storing LLM prompt templates
    """
    __tablename__ = "prompt_templates"
    
    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    reference_id = Column(String(255), unique=True, nullable=False, index=True)  # e.g., "prompt_ref_meta_v2_1"
    name = Column(String(255), nullable=False)  # Human-readable name
    type = Column(String(50), nullable=False, index=True)  # metadata, evaluation, clarification
    version = Column(String(50), nullable=False)  # Version string (e.g., "v2.1")
    
    # Prompt content
    system_prompt = Column(Text)  # System prompt (if applicable)
    user_prompt_template = Column(Text, nullable=False)  # User prompt template with placeholders
    description = Column(Text)  # Description of what this prompt does
    
    # Configuration
    variables = Column(JSON, default=dict)  # Available variables for template substitution
    config = Column(JSON, default=dict)  # Additional configuration (temperature, max_tokens, etc.)
    
    # Status
    is_active = Column(Boolean, default=True, index=True)  # Whether this template is active
    is_default = Column(Boolean, default=False, index=True)  # Default template for this type
    
    # Metadata
    usage_count = Column(String(20), default="0")  # Number of times this template has been used
    tags = Column(JSON, default=list)  # Tags for categorization
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    created_by = Column(String(255))  # User who created this template
    
    def __repr__(self):
        return f"<PromptTemplate(reference_id='{self.reference_id}', type='{self.type}', version='{self.version}')>"
    
    def to_dict(self):
        """Convert to dictionary"""
        return {
            "id": self.id,
            "reference_id": self.reference_id,
            "name": self.name,
            "type": self.type,
            "version": self.version,
            "system_prompt": self.system_prompt,
            "user_prompt_template": self.user_prompt_template,
            "description": self.description,
            "variables": self.variables or {},
            "config": self.config or {},
            "is_active": self.is_active,
            "is_default": self.is_default,
            "usage_count": int(self.usage_count) if self.usage_count else 0,
            "tags": self.tags or [],
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
            "created_by": self.created_by
        }

