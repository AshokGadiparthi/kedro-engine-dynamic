"""
Database models for job management.
"""

from enum import Enum
from datetime import datetime
from sqlalchemy import Column, String, DateTime, Text, Integer, Enum as SQLEnum, Index
from sqlalchemy.dialects.mysql import JSON

from app.core.database import Base


class JobStatus(str, Enum):
    """Job execution status"""
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


class Job(Base):
    """Pipeline execution job record."""
    
    __tablename__ = "jobs"
    
    id = Column(String(36), primary_key=True)
    pipeline_name = Column(String(255), nullable=False, index=True)
    user_id = Column(String(36), nullable=False, index=True)
    status = Column(SQLEnum(JobStatus), default=JobStatus.PENDING, index=True)
    parameters = Column(JSON, nullable=True)
    results = Column(JSON, nullable=True)
    error_message = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, index=True)
    started_at = Column(DateTime, nullable=True)
    completed_at = Column(DateTime, nullable=True)
    execution_time = Column(Integer, nullable=True)
    
    __table_args__ = (
        Index('idx_user_status', 'user_id', 'status'),
        Index('idx_pipeline_status', 'pipeline_name', 'status'),
    )
    
    def to_dict(self):
        """Convert to dictionary"""
        return {
            'id': self.id,
            'pipeline_name': self.pipeline_name,
            'user_id': self.user_id,
            'status': self.status.value if self.status else None,
            'parameters': self.parameters,
            'results': self.results,
            'error_message': self.error_message,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'started_at': self.started_at.isoformat() if self.started_at else None,
            'completed_at': self.completed_at.isoformat() if self.completed_at else None,
            'execution_time': self.execution_time
        }
