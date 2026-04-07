"""
# Architect: Meet Kumar
# InsightAI - Dataset Model
"""

import uuid
from datetime import datetime
from enum import Enum as PyEnum

from sqlalchemy import Column, String, Integer, DateTime, ForeignKey, Enum, Float, JSON
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship

from app.core.database import Base


class DatasetStatus(str, PyEnum):
    PENDING = "pending"
    UPLOADING = "uploading"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"


class Dataset(Base):
    __tablename__ = "datasets"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    
    # File information
    name = Column(String(255), nullable=False)
    file_path = Column(String(512), nullable=False)
    original_filename = Column(String(255), nullable=False)
    file_size = Column(Integer, nullable=False)  # in bytes
    file_hash = Column(String(64), nullable=True)  # SHA-256 hash
    
    # Data statistics
    row_count = Column(Integer, nullable=True)
    column_count = Column(Integer, nullable=True)
    column_schema = Column(JSON, nullable=True)  # {column_name: {type, nullable, unique_values, etc.}}
    
    # Processing status
    status = Column(Enum(DatasetStatus), default=DatasetStatus.PENDING, nullable=False)
    error_message = Column(String(1000), nullable=True)
    
    # Data quality
    data_health_score = Column(Float, nullable=True)  # 0-100
    missing_values_count = Column(Integer, nullable=True)
    duplicate_rows_count = Column(Integer, nullable=True)
    
    # Cleaning results
    cleaned_file_path = Column(String(512), nullable=True)
    cleaning_summary = Column(JSON, nullable=True)
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    processed_at = Column(DateTime, nullable=True)
    
    # Relationships
    user = relationship("User", back_populates="datasets")
    pipelines = relationship("CleaningPipeline", back_populates="dataset", cascade="all, delete-orphan")
    analysis_sessions = relationship("AnalysisSession", back_populates="dataset", cascade="all, delete-orphan")
    
    @property
    def file_size_formatted(self) -> str:
        """Format file size in human-readable format."""
        if self.file_size is None:
            return "Unknown"
        
        size = float(self.file_size)
        for unit in ['B', 'KB', 'MB', 'GB']:
            if size < 1024:
                return f"{size:.1f} {unit}"
            size /= 1024
        return f"{size:.1f} TB"

    def __repr__(self):
        return f"<Dataset(id={self.id}, name={self.name}, status={self.status})>"
    
    def to_dict(self, include_schema: bool = False):
        data = {
            "id": str(self.id),
            "user_id": str(self.user_id),
            "name": self.name,
            "original_filename": self.original_filename,
            "file_size": self.file_size,
            "file_size_formatted": self._format_file_size(),
            "row_count": self.row_count,
            "column_count": self.column_count,
            "status": self.status.value,
            "data_health_score": self.data_health_score,
            "missing_values_count": self.missing_values_count,
            "duplicate_rows_count": self.duplicate_rows_count,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
            "processed_at": self.processed_at.isoformat() if self.processed_at else None,
        }
        if include_schema:
            data["column_schema"] = self.column_schema
            data["cleaning_summary"] = self.cleaning_summary
        return data
    
    def _format_file_size(self) -> str:
        """Format file size in human-readable format."""
        if self.file_size is None:
            return "Unknown"
        for unit in ['B', 'KB', 'MB', 'GB']:
            if self.file_size < 1024:
                return f"{self.file_size:.1f} {unit}"
            self.file_size /= 1024
        return f"{self.file_size:.1f} TB"
