"""Data Cleaning Pipeline WITH PATH B FEATURE SCALING."""

import pandas as pd
import numpy as np
import logging
from typing import Tuple, Dict, Any
from sklearn.preprocessing import StandardScaler
from kedro.pipeline import Pipeline, node

logger = logging.getLogger(__name__)

def clean_data(
        df: pd.DataFrame,
        handle_missing: str = "median",
        remove_duplicates: bool = True,
) -> Tuple[pd.DataFrame, Dict[str, Any]]:
    """Clean data with PATH A + PATH B feature scaling.

    Args:
        df: DataFrame to clean
        handle_missing: Strategy for missing values (drop, median, mean)
        remove_duplicates: Whether to remove duplicate rows

    Returns:
        Tuple of (cleaned DataFrame, report dictionary)
    """
    logger.info("🧹 Cleaning data...")

    df_clean = df.copy()
    report: Dict[str, Any] = {"original_shape": df.shape, "actions": []}

    # ════════════════════════════════════════════════════════════════════════
    # ✨ PATH A: OUTLIER DETECTION & CAPPING
    # ════════════════════════════════════════════════════════════════════════

    logger.info("="*80)
    logger.info("🔍 STARTING OUTLIER DETECTION (PATH A)")
    logger.info("="*80)

    numeric_cols = df_clean.select_dtypes(include=['int64', 'float64']).columns.tolist()
    logger.info(f"Found {len(numeric_cols)} numeric columns for outlier detection")

    outliers_per_col = {}
    total_outliers = 0

    for col in numeric_cols:
        Q1 = df_clean[col].quantile(0.25)
        Q3 = df_clean[col].quantile(0.75)
        IQR = Q3 - Q1

        lower_bound = Q1 - 1.5 * IQR
        upper_bound = Q3 + 1.5 * IQR

        outlier_mask = (df_clean[col] < lower_bound) | (df_clean[col] > upper_bound)
        n_outliers = outlier_mask.sum()
        outliers_per_col[col] = n_outliers
        total_outliers += n_outliers

        if n_outliers > 0:
            logger.info(f"  Column '{col}': {n_outliers} outliers (bounds: [{lower_bound:.2f}, {upper_bound:.2f}])")

    logger.info(f"Total outliers found: {total_outliers} across {len(numeric_cols)} columns")

    logger.info("Capping outliers to reasonable bounds...")
    for col in numeric_cols:
        Q1 = df_clean[col].quantile(0.25)
        Q3 = df_clean[col].quantile(0.75)
        IQR = Q3 - Q1
        lower_bound = Q1 - 1.5 * IQR
        upper_bound = Q3 + 1.5 * IQR

        df_clean[col] = df_clean[col].clip(lower_bound, upper_bound)

    logger.info("✅ Outliers capped successfully")
    report["outliers_detected"] = total_outliers
    report["outliers_per_column"] = outliers_per_col
    report["actions"].append(f"Detected and capped {total_outliers} outliers")

    # ════════════════════════════════════════════════════════════════════════
    # ✨ PATH A: DUPLICATE DETECTION & REMOVAL
    # ════════════════════════════════════════════════════════════════════════

    logger.info("-"*80)
    logger.info("🔍 DUPLICATE DETECTION")
    logger.info("-"*80)

    if remove_duplicates:
        initial_rows = len(df_clean)
        df_clean = df_clean.drop_duplicates()
        n_removed = initial_rows - len(df_clean)

        if n_removed > 0:
            logger.info(f"Initial rows: {initial_rows}")
            logger.info(f"✅ Duplicates removed. Final rows: {len(df_clean)}")
            logger.info(f"   Rows deleted: {n_removed}")
            report["actions"].append(f"Removed {n_removed} duplicates")
            report["duplicates_removed"] = n_removed

    # ════════════════════════════════════════════════════════════════════════
    # Standard missing value handling
    # ════════════════════════════════════════════════════════════════════════

    logger.info("-"*80)
    logger.info("📊 HANDLING MISSING VALUES")
    logger.info("-"*80)

    logger.info(f"   Handling missing values with '{handle_missing}' strategy")

    if handle_missing == "drop":
        n_before = len(df_clean)
        df_clean = df_clean.dropna()
        n_dropped = n_before - len(df_clean)
        logger.info(f"   Dropped {n_dropped} rows with missing values")
        report["actions"].append(f"Dropped {n_dropped} rows with missing values")

    elif handle_missing == "median":
        numeric_cols = df_clean.select_dtypes(include=[np.number]).columns
        for col in numeric_cols:
            if df_clean[col].isnull().any():
                median_val = df_clean[col].median()
                df_clean[col].fillna(median_val, inplace=True)

        if len(numeric_cols) > 0:
            logger.info(f"   Filled {len(numeric_cols)} numeric columns with median")
            report["actions"].append(f"Filled {len(numeric_cols)} numeric columns with median")

    elif handle_missing == "mean":
        numeric_cols = df_clean.select_dtypes(include=[np.number]).columns
        for col in numeric_cols:
            if df_clean[col].isnull().any():
                mean_val = df_clean[col].mean()
                df_clean[col].fillna(mean_val, inplace=True)

    categorical_cols = df_clean.select_dtypes(include=['object']).columns
    for col in categorical_cols:
        if df_clean[col].isnull().any():
            mode_val = df_clean[col].mode()
            if len(mode_val) > 0:
                df_clean[col].fillna(mode_val[0], inplace=True)

    # ════════════════════════════════════════════════════════════════════════
    # ✨ PATH B: FEATURE SCALING (NEW)
    # ════════════════════════════════════════════════════════════════════════

    logger.info("-"*80)
    logger.info("📈 FEATURE SCALING (PATH B)")
    logger.info("="*80)

    # Get numeric columns for scaling
    numeric_cols_to_scale = df_clean.select_dtypes(include=['int64', 'float64']).columns.tolist()
    logger.info(f"Scaling {len(numeric_cols_to_scale)} numeric columns with StandardScaler...")

    if len(numeric_cols_to_scale) > 0:
        scaler = StandardScaler()
        df_clean[numeric_cols_to_scale] = scaler.fit_transform(df_clean[numeric_cols_to_scale])

        logger.info(f"✅ Feature scaling applied to:")
        for i, col in enumerate(numeric_cols_to_scale[:10]):  # Show first 10
            logger.info(f"   {i+1}. {col}")

        if len(numeric_cols_to_scale) > 10:
            logger.info(f"   ... and {len(numeric_cols_to_scale) - 10} more columns")

        logger.info("✅ All numeric features normalized to mean=0, std=1")
        report["features_scaled"] = numeric_cols_to_scale
        report["actions"].append(f"Scaled {len(numeric_cols_to_scale)} numeric features with StandardScaler")

    logger.info("="*80)

    report["final_shape"] = df_clean.shape
    report["rows_removed"] = df.shape[0] - df_clean.shape[0]

    logger.info(f"   ✅ Cleaned data shape: {df_clean.shape}")
    logger.info("="*80)

    return df_clean, report

def create_pipeline() -> Pipeline:
    """Create data cleaning pipeline with PATH B scaling."""
    return Pipeline(
        [
            node(
                func=clean_data,
                inputs=["raw_data", "params:data_processing.handle_missing"],
                outputs=["cleaned_data", "data_cleaning_report"],
                name="clean_data_node",
                tags=["data_cleaning"],
            ),
        ],
        tags=["data_cleaning"],
    )