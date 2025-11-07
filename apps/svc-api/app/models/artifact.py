"""
Artifact, Metadata, and Clarification models
"""

from sqlalchemy import Column, String, DateTime, JSON, Text, Integer, ForeignKey
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
import uuid

from db.database import Base

class Artifact(Base):
    """
    Document artifact model representing processed documents
    """
    __tablename__ = "artifacts"
    
    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    source_id = Column(String(36), ForeignKey("sources.id"), nullable=False, index=True)
    uri = Column(Text, nullable=False)  # Original URI/URL
    content_hash = Column(String(64), unique=True, nullable=False, index=True)  # SHA-256 hash
    mime_type = Column(String(100))
    version = Column(Integer, default=1)
    normalized_ref = Column(Text)  # Reference to normalized content in object store
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    # Relationships
    source = relationship("Source", backref="artifacts")
    document_metadata = relationship("DocumentMetadata", back_populates="artifact", uselist=False, cascade="all, delete-orphan")
    clarification = relationship("Clarification", back_populates="artifact", uselist=False, cascade="all, delete-orphan")
    evaluations = relationship("Evaluation", back_populates="artifact", cascade="all, delete-orphan")
    library_items = relationship("LibraryItem", back_populates="artifact", cascade="all, delete-orphan")
    
    def __repr__(self):
        return f"<Artifact(id='{self.id}', uri='{self.uri[:50]}...', hash='{self.content_hash[:8]}')>"

class DocumentMetadata(Base):
    """
    Document metadata extracted from artifacts
    """
    __tablename__ = "document_metadata"
    
    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    artifact_id = Column(String(36), ForeignKey("artifacts.id"), nullable=False, index=True)
    title = Column(Text)
    authors = Column(Text)  # JSON string of author names
    organization = Column(Text)
    pub_date = Column(DateTime(timezone=True))
    topics = Column(Text)  # JSON string of topic tags
    geo_location = Column(Text)  # Geographic scope/location
    language = Column(String(10))  # ISO language code
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    # Relationships
    artifact = relationship("Artifact", back_populates="document_metadata")
    
    def __repr__(self):
        return f"<DocumentMetadata(artifact_id='{self.artifact_id}', title='{self.title[:50] if self.title else None}')>"

class Clarification(Base):
    """
    Clarification signals and evidence for artifacts
    """
    __tablename__ = "clarifications"
    
    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    artifact_id = Column(String(36), ForeignKey("artifacts.id"), nullable=False, index=True)
    signals = Column(JSON, nullable=False, default=dict)  # Clarification signals (reputation, citations, etc.)
    evidence_ref = Column(Text)  # Reference to evidence in object store (WARC files, etc.)
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    # Relationships
    artifact = relationship("Artifact", back_populates="clarification")
    
    def __repr__(self):
        return f"<Clarification(artifact_id='{self.artifact_id}', signals_count={len(self.signals) if self.signals else 0})>"

