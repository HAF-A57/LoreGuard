"""
LibraryItem model for curated Signal documents
"""

from sqlalchemy import Column, DateTime, Text, Boolean, ForeignKey, String
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
import uuid

from db.database import Base

class LibraryItem(Base):
    """
    Library item model for curated Signal documents
    """
    __tablename__ = "library_items"
    
    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    artifact_id = Column(String(36), ForeignKey("artifacts.id"), nullable=False, index=True)
    snapshot_id = Column(String(36))  # Reference to specific version/snapshot
    tags = Column(Text)  # JSON string of curation tags
    is_signal = Column(Boolean, default=False, index=True)  # True for Signal documents
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    # Relationships
    artifact = relationship("Artifact", back_populates="library_items")
    
    def __repr__(self):
        return f"<LibraryItem(artifact_id='{self.artifact_id}', is_signal={self.is_signal})>"
    
    @property
    def evaluation(self):
        """Get the latest evaluation for this artifact"""
        if not self.artifact or not self.artifact.evaluations:
            return None
        
        # Return the most recent evaluation
        return max(self.artifact.evaluations, key=lambda e: e.created_at)
    
    @property
    def confidence_score(self) -> float:
        """Get confidence score from latest evaluation"""
        evaluation = self.evaluation
        return float(evaluation.confidence) if evaluation and evaluation.confidence else 0.0
    
    @property
    def total_score(self) -> float:
        """Get total score from latest evaluation"""
        evaluation = self.evaluation
        return evaluation.total_score if evaluation else 0.0

