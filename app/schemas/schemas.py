"""
Pydantic Schemas for all API endpoints
"""

from pydantic import BaseModel
from typing import Optional, Dict, Any, List
from datetime import datetime
from enum import Enum


# ============================================================================
# AUTHENTICATION SCHEMAS
# ============================================================================

class UserRegister(BaseModel):
    """User registration schema"""
    username: str
    email: Optional[str] = None
    password: str
    full_name: Optional[str] = None


class UserLogin(BaseModel):
    """User login schema"""
    username: str
    password: str


class UserResponse(BaseModel):
    """User response schema"""
    id: str
    username: str
    email: Optional[str] = None
    full_name: Optional[str] = None
    created_at: str


class TokenResponse(BaseModel):
    """Token response schema"""
    access_token: str
    token_type: str
    user: UserResponse


# ============================================================================
# PROJECT SCHEMAS
# ============================================================================

class ProjectCreate(BaseModel):
    """Create project schema"""
    name: str
    description: Optional[str] = None


class ProjectResponse(BaseModel):
    """Project response schema"""
    id: str
    name: str
    description: Optional[str] = None
    owner_id: str
    created_at: str


# ============================================================================
# DATASET SCHEMAS
# ============================================================================

class DatasetCreate(BaseModel):
    """Create dataset schema"""
    name: str
    project_id: str
    description: Optional[str] = None


class DatasetResponse(BaseModel):
    """Dataset response schema"""
    id: str
    name: str
    project_id: str
    description: Optional[str] = None
    created_at: str


# ============================================================================
# MODEL SCHEMAS
# ============================================================================

class ModelCreate(BaseModel):
    """Create model schema"""
    name: str
    project_id: str
    model_type: str
    description: Optional[str] = None


class ModelResponse(BaseModel):
    """Model response schema"""
    id: str
    name: str
    project_id: str
    model_type: str
    description: Optional[str] = None
    created_at: str


# ============================================================================
# ACTIVITY SCHEMAS
# ============================================================================

class ActivityCreate(BaseModel):
    """Create activity schema"""
    action: str
    entity_type: str
    entity_id: str
    details: Optional[Dict[str, Any]] = None


class ActivityResponse(BaseModel):
    """Activity response schema"""
    id: str
    user_id: str
    action: str
    entity_type: str
    entity_id: str
    details: Optional[Dict[str, Any]] = None
    created_at: str


# ============================================================================
# HEALTH SCHEMAS
# ============================================================================

class HealthResponse(BaseModel):
    """Health check response - Simple version"""
    status: str
    service: Optional[str] = None
    version: Optional[str] = None
    timestamp: datetime


# ============================================================================
# EDA SCHEMAS
# ============================================================================

class AnalysisResponse(BaseModel):
    """Response when analysis starts"""
    job_id: str
    dataset_id: str
    status: str
    message: str


class JobStatusEnum(str, Enum):
    """Job status enum"""
    pending = "pending"
    running = "running"
    completed = "completed"
    failed = "failed"
    cancelled = "cancelled"


class JobStatusResponse(BaseModel):
    """Job status response"""
    job_id: str
    dataset_id: str
    status: str
    progress: int
    current_phase: Optional[str] = None
    created_at: datetime
    updated_at: Optional[datetime] = None
    result_id: Optional[str] = None
    error: Optional[str] = None


# ============================================================================
# JOB SCHEMAS
# ============================================================================

class JobCreate(BaseModel):
    """Request schema for creating a job"""
    pipeline_name: str
    parameters: Optional[Dict[str, Any]] = {}
    tags: Optional[List[str]] = None

    class Config:
        json_schema_extra = {
            "example": {
                "pipeline_name": "data_processing",
                "parameters": {}
            }
        }


class JobResponse(BaseModel):
    """Response schema for job"""
    id: str
    pipeline_name: str
    user_id: str
    status: JobStatusEnum
    parameters: Optional[Dict[str, Any]] = None
    results: Optional[Dict[str, Any]] = None
    error_message: Optional[str] = None
    created_at: datetime
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    execution_time: Optional[int] = None
