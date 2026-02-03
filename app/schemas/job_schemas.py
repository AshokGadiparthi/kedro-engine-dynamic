"""
Pydantic schemas for job management API.
"""

from datetime import datetime
from typing import Dict, Optional, Any, List
from enum import Enum
from pydantic import BaseModel, Field


class JobStatusEnum(str, Enum):
    """Job status enum"""
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


class JobCreate(BaseModel):
    """Request schema for creating a job"""
    
    pipeline_name: str = Field(..., min_length=1, description="Pipeline to execute")
    parameters: Optional[Dict[str, Any]] = Field(None, description="Pipeline parameters")
    tags: Optional[List[str]] = Field(None, description="Node tags to execute")
    
    class Config:
        json_schema_extra = {
            "example": {
                "pipeline_name": "data_processing",
                "parameters": {}
            }
        }


class JobResponse(BaseModel):
    """Response schema for job"""
    
    id: str = Field(..., description="Job ID")
    pipeline_name: str = Field(..., description="Pipeline name")
    user_id: str = Field(..., description="User ID")
    status: JobStatusEnum = Field(..., description="Status")
    parameters: Optional[Dict[str, Any]] = Field(None, description="Parameters")
    results: Optional[Dict[str, Any]] = Field(None, description="Results")
    error_message: Optional[str] = Field(None, description="Error message")
    created_at: datetime = Field(..., description="Created at")
    started_at: Optional[datetime] = Field(None, description="Started at")
    completed_at: Optional[datetime] = Field(None, description="Completed at")
    execution_time: Optional[int] = Field(None, description="Execution time")
    
    class Config:
        from_attributes = True


class JobListResponse(BaseModel):
    """Response schema for job list"""
    
    total: int
    jobs: List[JobResponse]
    offset: int = 0
    limit: int = 100


class JobStatsResponse(BaseModel):
    """Response schema for job statistics"""
    
    total: int
    pending: int
    running: int
    completed: int
    failed: int
    cancelled: int
