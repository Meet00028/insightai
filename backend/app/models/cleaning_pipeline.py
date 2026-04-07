"""
# Architect: Meet Kumar
# InsightAI - Cleaning Pipeline Model
"""

import uuid
from datetime import datetime

from sqlalchemy import Column, String, DateTime, ForeignKey, Boolean, JSON, Integer
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship

from app.core.database import Base


class CleaningPipeline(Base):
    __tablename__ = "cleaning_pipelines"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    dataset_id = Column(UUID(as_uuid=True), ForeignKey("datasets.id", ondelete="CASCADE"), nullable=True, index=True)
    
    # Pipeline info
    name = Column(String(255), nullable=False)
    description = Column(String(1000), nullable=True)
    
    # Steps stored as JSON array
    # Each step: {"operation": "drop_na", "params": {"columns": ["col1", "col2"]}, "order": 1}
    steps = Column(JSON, default=list, nullable=False)
    
    # Template flag for reusable pipelines
    is_template = Column(Boolean, default=False, nullable=False)
    is_public = Column(Boolean, default=False, nullable=False)
    
    # Usage statistics
    usage_count = Column(Integer, default=0)
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    
    # Relationships
    user = relationship("User", back_populates="pipelines")
    dataset = relationship("Dataset", back_populates="pipelines")
    
    def __repr__(self):
        return f"<CleaningPipeline(id={self.id}, name={self.name}, steps_count={len(self.steps or [])})>"
    
    def to_dict(self):
        return {
            "id": str(self.id),
            "user_id": str(self.user_id),
            "dataset_id": str(self.dataset_id) if self.dataset_id else None,
            "name": self.name,
            "description": self.description,
            "steps": self.steps or [],
            "is_template": self.is_template,
            "is_public": self.is_public,
            "usage_count": self.usage_count,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }
    
    def add_step(self, operation: str, params: dict, order: int = None):
        """Add a cleaning step to the pipeline."""
        if self.steps is None:
            self.steps = []
        
        if order is None:
            order = len(self.steps) + 1
        
        step = {
            "id": str(uuid.uuid4()),
            "operation": operation,
            "params": params,
            "order": order,
            "created_at": datetime.utcnow().isoformat(),
        }
        self.steps.append(step)
        self.steps.sort(key=lambda x: x["order"])
        return step
    
    def remove_step(self, step_id: str):
        """Remove a step from the pipeline."""
        if self.steps:
            self.steps = [s for s in self.steps if s["id"] != step_id]
            # Reorder remaining steps
            for i, step in enumerate(sorted(self.steps, key=lambda x: x["order"]), 1):
                step["order"] = i
    
    def reorder_steps(self, step_ids: list):
        """Reorder steps based on provided step IDs."""
        if not self.steps:
            return
        
        step_map = {s["id"]: s for s in self.steps}
        self.steps = []
        for i, step_id in enumerate(step_ids, 1):
            if step_id in step_map:
                step_map[step_id]["order"] = i
                self.steps.append(step_map[step_id])
