"""
Evaluation model for LLM assessment results
"""

from sqlalchemy import Column, String, DateTime, JSON, ForeignKey, DECIMAL
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
import uuid

from db.database import Base

class Evaluation(Base):
    """
    LLM evaluation results for artifacts
    """
    __tablename__ = "evaluations"
    
    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    artifact_id = Column(String(36), ForeignKey("artifacts.id"), nullable=False, index=True)
    rubric_version = Column(String(50), ForeignKey("rubrics.version"), nullable=False, index=True)
    model_id = Column(String(100), nullable=False)  # LLM model identifier
    scores = Column(JSON, nullable=False)  # Detailed scores by category
    label = Column(String(50), index=True)  # Signal, Review, Noise
    confidence = Column(DECIMAL(3, 2))  # Confidence score 0.00-1.00
    prompt_ref = Column(String(255))  # Reference to prompt used
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    # Relationships
    artifact = relationship("Artifact", back_populates="evaluations")
    rubric = relationship("Rubric", back_populates="evaluations")
    
    def __repr__(self):
        return f"<Evaluation(artifact_id='{self.artifact_id}', label='{self.label}', confidence={self.confidence})>"
    
    @property
    def total_score(self) -> float:
        """Calculate weighted total score"""
        if not self.scores or not self.rubric:
            return 0.0
        
        total = 0.0
        for category, score_data in self.scores.items():
            if category in self.rubric.categories:
                weight = self.rubric.categories[category].get('weight', 0)
                score = score_data.get('score', 0) if isinstance(score_data, dict) else score_data
                total += score * weight
        
        return total
    
    def get_category_score(self, category: str) -> float:
        """Get score for specific category"""
        if not self.scores or category not in self.scores:
            return 0.0
        
        score_data = self.scores[category]
        return score_data.get('score', 0) if isinstance(score_data, dict) else score_data

