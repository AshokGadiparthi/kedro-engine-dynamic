"""Database Models"""
from sqlalchemy import Column, String, DateTime, Text, Integer, Boolean,ForeignKey,Float,Index
from sqlalchemy.sql import func
from uuid import uuid4
from app.core.database import Base

from sqlalchemy.orm import relationship
from datetime import datetime

class User(Base):
    """User model"""
    __tablename__ = "users"
    
    id = Column(String, primary_key=True)
    username = Column(String, unique=True, index=True)
    email = Column(String, unique=True, index=True, nullable=True)
    password_hash = Column(String)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

class Workspace(Base):
    """Workspace model"""
    __tablename__ = "workspaces"

    id = Column(String, primary_key=True)
    name = Column(String, index=True)
    slug = Column(String, unique=True, index=True)
    description = Column(Text, nullable=True)
    owner_id = Column(String, index=True)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

class Project(Base):
    """Project model"""
    __tablename__ = "projects"
    
    id = Column(String, primary_key=True)
    name = Column(String, index=True)
    description = Column(Text, nullable=True)
    owner_id = Column(String, index=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

class Dataset(Base):
    """Dataset model"""
    __tablename__ = "datasets"
    
    id = Column(String, primary_key=True)
    name = Column(String, index=True)
    project_id = Column(String, index=True)
    description = Column(Text, nullable=True)
    file_name = Column(String(255), nullable=True)  # ✅ Changed from file_path
    file_size_bytes = Column(Integer, nullable=True)  # ✅ Changed from file_size
    file_path = Column(String, index=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

class Activity(Base):
    """Activity model"""
    __tablename__ = "activities"
    
    id = Column(String, primary_key=True, default=lambda: str(uuid4()))
    user_id = Column(String, index=True)
    project_id = Column(String(36), ForeignKey("projects.id"), nullable=True)  # ✅ KEEP THIS
    action = Column(String)
    entity_type = Column(String)
    entity_id = Column(String)
    details = Column(Text, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())



class EdaResult(Base):
    """EDA Analysis Results - stores all analysis data"""
    __tablename__ = "eda_results"
    
    id = Column(String, primary_key=True, default=lambda: str(uuid4()))
    dataset_id = Column(String, index=True, unique=True)
    user_id = Column(String, index=True)
    
    # Summary data (JSON stored as text)
    summary = Column(Text)  # {shape, columns, dtypes, memory_usage}
    
    # Statistics data (JSON stored as text)
    statistics = Column(Text)  # {basic_stats, missing_values, duplicates}
    
    # Quality metrics (JSON stored as text)
    quality = Column(Text)  # {completeness, uniqueness, validity, consistency, etc}
    
    # Correlations (JSON stored as text)
    correlations = Column(Text)  # {correlations dict, threshold}
    
    # Metadata
    analysis_status = Column(String, default="completed")
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

# ============================================================================
# EDA RESULT MODELS - Store analysis results in database
# ============================================================================

class EDASummary(Base):
    """EDA Summary - Basic profile information"""
    __tablename__ = "eda_summary"
    
    id = Column(String, primary_key=True, default=lambda: str(uuid4()))
    dataset_id = Column(String, unique=True, index=True)
    shape_rows = Column(Integer)
    shape_cols = Column(Integer)
    columns = Column(Text)  # JSON string of column names
    dtypes = Column(Text)  # JSON string of column dtypes
    memory_usage = Column(String)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

class EDAStatistics(Base):
    """EDA Statistics - Descriptive statistics"""
    __tablename__ = "eda_statistics"
    
    id = Column(String, primary_key=True, default=lambda: str(uuid4()))
    dataset_id = Column(String, unique=True, index=True)
    basic_stats = Column(Text)  # JSON string of describe() results
    missing_values = Column(Text)  # JSON string of missing values by column
    duplicates = Column(Integer)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

class EDAQuality(Base):
    """EDA Quality Report - Data quality metrics"""
    __tablename__ = "eda_quality"
    
    id = Column(String, primary_key=True, default=lambda: str(uuid4()))
    dataset_id = Column(String, unique=True, index=True)
    completeness = Column(String)  # Percentage as string
    uniqueness = Column(String)
    validity = Column(String)
    consistency = Column(String)
    duplicate_rows = Column(Integer)
    missing_values_count = Column(Integer)
    total_cells = Column(Integer)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

class EDACorrelations(Base):
    """EDA Correlations - Correlation matrix"""
    __tablename__ = "eda_correlations"
    
    id = Column(String, primary_key=True, default=lambda: str(uuid4()))
    dataset_id = Column(String, unique=True, index=True)
    correlations = Column(Text)  # JSON string of correlations
    threshold = Column(String)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

class Datasource(Base):
    """Datasource model"""
    __tablename__ = "datasources"
    
    id = Column(String, primary_key=True)
    name = Column(String, index=True)
    type = Column(String)
    description = Column(Text, nullable=True)
    project_id = Column(String, index=True)
    host = Column(String, nullable=True)
    port = Column(Integer, nullable=True)
    database_name = Column(String, nullable=True)
    username = Column(String, nullable=True)
    password = Column(String, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

class Model(Base):
    """ML Model model"""
    __tablename__ = "models"
    
    id = Column(String, primary_key=True)
    name = Column(String, index=True)
    project_id = Column(String, index=True)
    description = Column(Text, nullable=True)
    model_type = Column(String)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

class Job(Base):
    """Pipeline job execution model"""
    __tablename__ = "jobs"

    id = Column(String(36), primary_key=True, index=True)
    pipeline_name = Column(String(255), nullable=False)
    user_id = Column(String(36), nullable=True)
    status = Column(String(50), default="pending")  # pending, running, completed, failed
    parameters = Column(Text, default="{}")  # JSON string
    results = Column(Text, nullable=True)  # JSON string
    error_message = Column(Text, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    started_at = Column(DateTime, nullable=True)
    completed_at = Column(DateTime, nullable=True)
    execution_time = Column(Float, nullable=True)  # seconds

    def __repr__(self):
        return f"<Job {self.id}: {self.pipeline_name} - {self.status}>"


# ============================================================================
# MODEL REGISTRY TABLES
# ============================================================================
# Add these imports at the top of models.py:
#   from sqlalchemy import Index
#   from sqlalchemy.orm import relationship
#   from datetime import datetime
# ============================================================================

class RegisteredModel(Base):
    """
    A registered model in the Model Registry.
    Each project can have multiple registered models.
    Each registered model can have multiple versions (from retraining).
    """

    __tablename__ = "registered_models"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid4()))
    project_id = Column(String(36), ForeignKey("projects.id", ondelete="CASCADE"), nullable=False, index=True)

    # Basic Info
    name = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)
    problem_type = Column(String(50), nullable=True)

    # Current best version info (denormalized for fast listing)
    current_version = Column(String(20), nullable=True)
    latest_version = Column(String(20), nullable=True)
    total_versions = Column(Integer, default=1)

    # Status: draft, staging, production, archived, deprecated
    status = Column(String(20), default="draft")

    # Best metrics (denormalized from best version)
    best_accuracy = Column(Float, nullable=True)
    best_algorithm = Column(String(100), nullable=True)

    # Deployment info
    is_deployed = Column(Boolean, default=False)
    deployment_url = Column(String(500), nullable=True)
    deployed_version = Column(String(20), nullable=True)
    deployed_at = Column(DateTime, nullable=True)

    # Source tracking
    source_dataset_id = Column(String(36), nullable=True)
    source_dataset_name = Column(String(255), nullable=True)
    training_job_id = Column(String(100), nullable=True)

    # Metadata (JSON text for SQLite)
    tags = Column(Text, nullable=True)
    labels = Column(Text, nullable=True)

    # Ownership
    created_by = Column(String(100), nullable=True)

    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    # Relationships
    versions = relationship(
        "ModelVersion",
        back_populates="registered_model",
        cascade="all, delete-orphan",
        order_by="ModelVersion.version_number.desc()"
    )

    __table_args__ = (
        Index("ix_registered_models_project_status", "project_id", "status"),
    )

    def __repr__(self):
        return f"<RegisteredModel(id={self.id}, name={self.name}, status={self.status})>"


class ModelVersion(Base):
    """
    A specific version of a registered model.
    Each training run (job) can produce one version.
    """

    __tablename__ = "model_versions"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid4()))
    model_id = Column(String(36), ForeignKey("registered_models.id", ondelete="CASCADE"), nullable=False, index=True)

    # Version info
    version = Column(String(20), nullable=False)
    version_number = Column(Integer, nullable=False)
    is_current = Column(Boolean, default=False)

    # Status: draft, staging, production, archived
    status = Column(String(20), default="draft")

    # Algorithm info
    algorithm = Column(String(100), nullable=True)

    # Metrics
    accuracy = Column(Float, nullable=True)
    precision = Column(Float, nullable=True)
    recall = Column(Float, nullable=True)
    f1_score = Column(Float, nullable=True)
    train_score = Column(Float, nullable=True)
    test_score = Column(Float, nullable=True)
    roc_auc = Column(Float, nullable=True)

    # Training info
    job_id = Column(String(100), nullable=True)
    training_time_seconds = Column(Float, nullable=True)
    model_size_mb = Column(Float, nullable=True)

    # Configuration (JSON text for SQLite)
    hyperparameters = Column(Text, nullable=True)
    feature_names = Column(Text, nullable=True)
    feature_importances = Column(Text, nullable=True)
    confusion_matrix = Column(Text, nullable=True)
    training_config = Column(Text, nullable=True)

    # Metadata
    tags = Column(Text, nullable=True)
    description = Column(Text, nullable=True)
    created_by = Column(String(100), nullable=True)

    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    # Relationships
    registered_model = relationship("RegisteredModel", back_populates="versions")
    artifacts = relationship("ModelArtifact", back_populates="model_version", cascade="all, delete-orphan")

    __table_args__ = (
        Index("ix_model_versions_model_current", "model_id", "is_current"),
    )

    def __repr__(self):
        return f"<ModelVersion(model_id={self.model_id}, version={self.version}, algo={self.algorithm})>"


class ModelArtifact(Base):
    """
    A file artifact associated with a model version.
    Types: model (.pkl), scaler (.pkl), plot (.png), report (.json/.csv)
    """

    __tablename__ = "model_artifacts"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid4()))
    model_version_id = Column(String(36), ForeignKey("model_versions.id", ondelete="CASCADE"), nullable=False, index=True)

    # Artifact info
    artifact_name = Column(String(255), nullable=False)
    artifact_type = Column(String(50), nullable=False)
    file_path = Column(String(500), nullable=False)
    file_size_bytes = Column(Integer, nullable=True)

    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    # Relationships
    model_version = relationship("ModelVersion", back_populates="artifacts")

    def __repr__(self):
        return f"<ModelArtifact(name={self.artifact_name}, type={self.artifact_type})>"