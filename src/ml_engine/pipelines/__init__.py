"""
ML Engine Pipelines.
"""

"""Pipeline modules."""

from .data_loading import create_pipeline as create_data_loading_pipeline
from .data_validation import create_pipeline as create_data_validation_pipeline
from .data_cleaning import create_pipeline as create_data_cleaning_pipeline

# PERFECT Phase 2: Import create_pipeline factory functions (NOT individual nodes)
from .feature_engineering import create_pipeline as create_feature_engineering_pipeline
from .feature_selection import create_pipeline as create_feature_selection_pipeline

# Optional: Phase 3 model training
try:
    from .model_training import create_pipeline as create_model_training_pipeline
except ImportError:
    create_model_training_pipeline = None


__all__ = [
    "create_data_loading_pipeline",
    "create_data_validation_pipeline",
    "create_data_cleaning_pipeline",
    # PERFECT Phase 2 pipeline factories
    "create_feature_engineering_pipeline",
    "create_feature_selection_pipeline",
    # Phase 3 (optional)
    "create_model_training_pipeline",
]