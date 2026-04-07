"""
# Architect: Meet Kumar
# InsightAI - Analysis Session Model
"""

import uuid
from datetime import datetime
from enum import Enum as PyEnum

from sqlalchemy import Column, String, DateTime, ForeignKey, Enum, JSON, Text, Integer
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship

from app.core.database import Base


class AnalysisStatus(str, PyEnum):
    QUEUED = "queued"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


class AnalysisSession(Base):
    __tablename__ = "analysis_sessions"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    dataset_id = Column(UUID(as_uuid=True), ForeignKey("datasets.id", ondelete="CASCADE"), nullable=False, index=True)
    
    # Analysis info
    query = Column(Text, nullable=True)  # User's natural language query
    analysis_type = Column(String(50), nullable=True)  # "cleaning", "exploration", "visualization", etc.
    
    # Status
    status = Column(Enum(AnalysisStatus), default=AnalysisStatus.QUEUED, nullable=False)
    error_message = Column(Text, nullable=True)
    
    # Agent thought process stored as JSON array
    # Each thought: {"timestamp": "...", "type": "thinking|action|result", "content": "..."}
    thought_process = Column(JSON, default=list)
    
    # Results
    result_summary = Column(JSON, nullable=True)
    generated_code = Column(Text, nullable=True)
    output_files = Column(JSON, nullable=True)  # Paths to generated charts, cleaned data, etc.
    insights = Column(JSON, nullable=True)  # Extracted insights from the analysis
    
    # Performance metrics
    started_at = Column(DateTime, nullable=True)
    completed_at = Column(DateTime, nullable=True)
    duration_seconds = Column(Integer, nullable=True)
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    
    # Relationships
    user = relationship("User", back_populates="analysis_sessions")
    dataset = relationship("Dataset", back_populates="analysis_sessions")
    
    def __repr__(self):
        return f"<AnalysisSession(id={self.id}, status={self.status})>"
    
    def to_dict(self, include_thoughts: bool = False):
        data = {
            "id": str(self.id),
            "user_id": str(self.user_id),
            "dataset_id": str(self.dataset_id),
            "query": self.query,
            "analysis_type": self.analysis_type,
            "status": self.status.value,
            "result_summary": self.result_summary,
            "insights": self.insights,
            "output_files": self.output_files,
            "duration_seconds": self.duration_seconds,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
            "started_at": self.started_at.isoformat() if self.started_at else None,
            "completed_at": self.completed_at.isoformat() if self.completed_at else None,
        }
        if include_thoughts:
            data["thought_process"] = self.thought_process or []
            data["generated_code"] = self.generated_code
        return data
    
    def add_thought(self, thought_type: str, content: str, metadata: dict = None):
        """Add a thought to the thought process."""
        if self.thought_process is None:
            self.thought_process = []
        
        thought = {
            "id": str(uuid.uuid4()),
            "timestamp": datetime.utcnow().isoformat(),
            "type": thought_type,  # "thinking", "action", "observation", "result", "error"
            "content": content,
        }
        if metadata:
            thought["metadata"] = metadata
        
        self.thought_process.append(thought)
        return thought
    
    def start(self):
        """Mark the analysis as started."""
        self.status = AnalysisStatus.RUNNING
        self.started_at = datetime.utcnow()
    
    def complete(self, result_summary: dict = None):
        """Mark the analysis as completed."""
        self.status = AnalysisStatus.COMPLETED
        self.completed_at = datetime.utcnow()
        if self.started_at:
            self.duration_seconds = int((self.completed_at - self.started_at).total_seconds())
        if result_summary:
            self.result_summary = result_summary
    
    def fail(self, error_message: str):
        """Mark the analysis as failed."""
        self.status = AnalysisStatus.FAILED
        self.error_message = error_message
        self.completed_at = datetime.utcnow()
        if self.started_at:
            self.duration_seconds = int((self.completed_at - self.started_at).total_seconds())
