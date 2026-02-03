"""End-to-End Pipeline."""

from kedro.pipeline import Pipeline
from ml_engine.pipelines.data_loading import create_pipeline as data_loading_pipeline
from ml_engine.pipelines.data_validation import create_pipeline as data_validation_pipeline
from ml_engine.pipelines.data_cleaning import create_pipeline as data_cleaning_pipeline

def create_pipeline() -> Pipeline:
    """Create end-to-end data processing pipeline."""
    return (
        data_loading_pipeline()
        + data_validation_pipeline()
        + data_cleaning_pipeline()
    )
