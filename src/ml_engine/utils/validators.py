"""Data validation utilities."""

import pandas as pd
import numpy as np
from typing import Dict, Any
from ml_engine.utils.exceptions import DataValidationError, InsufficientDataError
from ml_engine.utils.logger import get_logger

logger = get_logger(__name__)

def validate_dataframe(df: pd.DataFrame, min_rows: int = 10, min_cols: int = 2) -> Dict[str, Any]:
    """Validate DataFrame structure and content."""
    report = {
        "valid": True,
        "errors": [],
        "warnings": [],
        "stats": {
            "rows": len(df),
            "columns": len(df.columns),
            "memory_mb": float(df.memory_usage(deep=True).sum() / 1024**2),
        }
    }
    
    if len(df) < min_rows:
        report["errors"].append(f"Too few rows: {len(df)} < {min_rows}")
    
    if len(df.columns) < min_cols:
        report["errors"].append(f"Too few columns: {len(df.columns)} < {min_cols}")
    
    empty_cols = df.columns[df.isnull().all()].tolist()
    if empty_cols:
        report["errors"].append(f"Empty columns: {empty_cols}")
    
    n_duplicates = int(df.duplicated().sum())
    if n_duplicates > 0:
        report["warnings"].append(f"{n_duplicates} duplicate rows found")
    
    missing = df.isnull().sum()
    high_missing = missing[missing > len(df) * 0.5].index.tolist()
    if high_missing:
        report["warnings"].append(f"High missing values: {high_missing}")
    
    report["valid"] = len(report["errors"]) == 0
    return report

def validate_X_y(X: pd.DataFrame, y: pd.Series) -> bool:
    """Validate features and target alignment."""
    if X is None or y is None:
        raise DataValidationError("X and y cannot be None")
    
    if len(X) != len(y):
        raise DataValidationError(f"X and y length mismatch: {len(X)} vs {len(y)}")
    
    if len(X) < 10:
        raise InsufficientDataError(f"Need at least 10 samples, got {len(X)}")
    
    return True
