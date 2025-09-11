"""
Rubric model for evaluation criteria
"""

from sqlalchemy import Column, String, DateTime, JSON, Boolean
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
import uuid

from db.database import Base

class Rubric(Base):
    """
    Evaluation rubric model defining scoring criteria
    """
    __tablename__ = "rubrics"
    
    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    version = Column(String(50), unique=True, nullable=False, index=True)
    categories = Column(JSON, nullable=False)  # Scoring categories with weights and guidance
    thresholds = Column(JSON, nullable=False)  # Score thresholds for Signal/Review/Noise
    prompts = Column(JSON, nullable=False)  # LLM prompts for different evaluation stages
    is_active = Column(Boolean, default=False, index=True)  # Only one active rubric at a time
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    # Relationships
    evaluations = relationship("Evaluation", back_populates="rubric")
    
    def __repr__(self):
        return f"<Rubric(version='{self.version}', active={self.is_active})>"
    
    @property
    def category_names(self):
        """Get list of category names"""
        return list(self.categories.keys()) if self.categories else []
    
    @property
    def total_weight(self):
        """Calculate total weight of all categories"""
        if not self.categories:
            return 0
        return sum(cat.get('weight', 0) for cat in self.categories.values())
    
    def get_label_for_score(self, score: float) -> str:
        """Determine label based on score and thresholds"""
        if not self.thresholds:
            return "unknown"
        
        signal_min = self.thresholds.get('signal_min', 3.8)
        review_min = self.thresholds.get('review_min', 2.8)
        
        if score >= signal_min:
            return "Signal"
        elif score >= review_min:
            return "Review"
        else:
            return "Noise"

