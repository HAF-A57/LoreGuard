"""
Job model for workflow and task tracking
"""

from sqlalchemy import Column, String, DateTime, JSON, Integer, Text
from sqlalchemy.sql import func
import uuid

from db.database import Base

class Job(Base):
    """
    Job tracking model for workflows and background tasks
    """
    __tablename__ = "jobs"
    
    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    type = Column(String(100), nullable=False, index=True)  # ingest, normalize, evaluate, etc.
    status = Column(String(50), default="pending", index=True)  # pending, running, completed, failed
    timeline = Column(JSON, default=list)  # Array of status changes with timestamps
    retries = Column(Integer, default=0)
    error = Column(Text)  # Error message if failed
    payload = Column(JSON)  # Job-specific data
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    
    def __repr__(self):
        return f"<Job(id='{self.id}', type='{self.type}', status='{self.status}')>"
    
    def add_timeline_entry(self, status: str, message: str = None):
        """Add entry to job timeline"""
        if not self.timeline:
            self.timeline = []
        
        entry = {
            "timestamp": func.now().isoformat(),
            "status": status,
            "message": message
        }
        
        self.timeline.append(entry)
        self.status = status
    
    @property
    def duration_seconds(self) -> float:
        """Calculate job duration in seconds"""
        if not self.timeline or len(self.timeline) < 2:
            return 0.0
        
        from datetime import datetime
        start_time = datetime.fromisoformat(self.timeline[0]["timestamp"])
        end_time = datetime.fromisoformat(self.timeline[-1]["timestamp"])
        
        return (end_time - start_time).total_seconds()
    
    @property
    def is_terminal(self) -> bool:
        """Check if job is in terminal state"""
        return self.status in ["completed", "failed", "cancelled"]

