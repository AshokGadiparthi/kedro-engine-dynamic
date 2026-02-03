"""Data Validation Pipeline - Kedro 0.19.5 Compatible."""

import pandas as pd
import logging
from typing import Dict, Any
from kedro.pipeline import Pipeline, node
from ml_engine.utils.validators import validate_dataframe

logger = logging.getLogger(__name__)

def validate_data_quality(df: pd.DataFrame) -> Dict[str, Any]:
    """Validate data quality and generate report.
    
    Args:
        df: DataFrame to validate
        
    Returns:
        Validation report
    """
    logger.info("🔍 Validating data quality...")
    
    report = validate_dataframe(df)
    
    logger.info(f"   Rows: {report['stats']['rows']}")
    logger.info(f"   Columns: {report['stats']['columns']}")
    logger.info(f"   Memory: {report['stats']['memory_mb']:.2f} MB")
    
    if report["errors"]:
        for error in report["errors"]:
            logger.error(f"   ❌ {error}")
    
    if report["warnings"]:
        for warning in report["warnings"]:
            logger.warning(f"   ⚠️  {warning}")
    
    if report["valid"]:
        logger.info("   ✅ Validation passed")
    else:
        logger.error("   ❌ Validation failed")
    
    return report

def create_pipeline() -> Pipeline:
    """Create data validation pipeline."""
    return Pipeline(
        [
            node(
                func=validate_data_quality,
                inputs="raw_data",
                outputs="data_validation_report",
                name="validate_data_quality_node",
                tags=["data_validation"],
            ),
        ],
        tags=["data_validation"],
    )
