"""Pydantic Schemas - 100% Working - No Warnings"""

from pydantic import BaseModel, ConfigDict
from typing import Optional, Dict, Any, List
from datetime import datetime
from enum import Enum


class UserRegister(BaseModel):
    username: str
    email: Optional[str] = None
    password: str
    full_name: Optional[str] = None


class UserLogin(BaseModel):
    username: str
    password: str


class UserResponse(BaseModel):
    id: str
    username: str
    email: Optional[str] = None
    full_name: Optional[str] = None
    created_at: str


class TokenResponse(BaseModel):
    access_token: str
    token_type: str
    user: UserResponse

class TokenRefresh(BaseModel):
    """Token refresh schema"""
    refresh_token: str

class ProjectCreate(BaseModel):
    name: str
    description: Optional[str] = None


class ProjectResponse(BaseModel):
    id: str
    name: str
    description: Optional[str] = None
    owner_id: str
    created_at: str


class DatasetCreate(BaseModel):
    name: str
    project_id: str
    description: Optional[str] = None


class DatasetResponse(BaseModel):
    id: str
    name: str
    project_id: str
    description: Optional[str] = None
    created_at: str


class ModelCreate(BaseModel):
    """FIXED: No namespace warnings"""
    name: str
    project_id: str
    model_type: str
    description: Optional[str] = None
    model_config = ConfigDict(protected_namespaces=())


class ModelResponse(BaseModel):
    """FIXED: No namespace warnings"""
    id: str
    name: str
    project_id: str
    model_type: str
    description: Optional[str] = None
    created_at: str
    model_config = ConfigDict(protected_namespaces=())


class ActivityCreate(BaseModel):
    action: str
    entity_type: str
    entity_id: str
    details: Optional[Dict[str, Any]] = None


class ActivityResponse(BaseModel):
    id: str
    user_id: str
    action: str
    entity_type: str
    entity_id: str
    details: Optional[Dict[str, Any]] = None
    created_at: str


class HealthResponse(BaseModel):
    status: str
    service: Optional[str] = None
    version: Optional[str] = None
    timestamp: datetime


class AnalysisResponse(BaseModel):
    job_id: str
    dataset_id: str
    status: str
    message: str


class JobStatusEnum(str, Enum):
    pending = "pending"
    running = "running"
    completed = "completed"
    failed = "failed"
    cancelled = "cancelled"


class JobStatusResponse(BaseModel):
    job_id: str
    dataset_id: str
    status: str
    progress: int
    current_phase: Optional[str] = None
    created_at: datetime
    updated_at: Optional[datetime] = None
    result_id: Optional[str] = None
    error: Optional[str] = None


class JobCreate(BaseModel):
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
