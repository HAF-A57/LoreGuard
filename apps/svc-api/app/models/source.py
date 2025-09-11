"""
Source model for data sources
"""

from sqlalchemy import Column, String, DateTime, JSON, ARRAY, Text
from sqlalchemy.sql import func
import uuid

from db.database import Base

class Source(Base):
    """
    Data source model representing external sources of documents
    """
    __tablename__ = "sources"
    
    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    name = Column(String(255), nullable=False, index=True)
    type = Column(String(50), nullable=False)  # web, api, feed, etc.
    config = Column(JSON, nullable=False, default=dict)  # Source-specific configuration
    schedule = Column(String(100))  # Cron-like schedule string
    status = Column(String(50), default="active", index=True)  # active, paused, error
    last_run = Column(DateTime(timezone=True))
    tags = Column(Text)  # JSON string of tags for categorization
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    
    def __repr__(self):
        return f"<Source(name='{self.name}', type='{self.type}', status='{self.status}')>"

