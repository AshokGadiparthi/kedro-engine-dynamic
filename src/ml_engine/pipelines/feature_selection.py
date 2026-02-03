"""
COMPLETE FINAL PHASE 2 - FEATURE SELECTION WITH REAL TARGET (DICT TO DATAFRAME FIX)
=====================================================================
Replaces: src/ml_engine/pipelines/feature_selection.py

CRITICAL FIX: Convert dicts to DataFrames for CSV saving
=====================================================================
"""

import pandas as pd
import numpy as np
from sklearn.ensemble import RandomForestClassifier, RandomForestRegressor
from sklearn.inspection import permutation_importance
from typing import Dict, Any, Tuple
import logging
from kedro.pipeline import Pipeline, node

log = logging.getLogger(__name__)


# ============================================================================
# GAP 2 FIX: PROBLEM TYPE DETECTION (HANDLES DATAFRAME OR SERIES)
# ============================================================================

def detect_problem_type(
        y: pd.DataFrame,
        params: Dict[str, Any]
) -> Dict[str, Any]:
    """
    Detect classification vs regression (Gap 2 Fix).

    ULTRA-FIXED: Now handles y_train as DataFrame (from CSV) or Series

    Args:
        y: Target variable (DataFrame or Series)
        params: May contain manual 'problem_type' override

    Returns:
        Detection result
    """
    print(f"\n{'='*80}")
    print(f"🎯 PROBLEM TYPE DETECTION (Gap 2 Fix)")
    print(f"{'='*80}")

    # Convert DataFrame to Series if needed
    if isinstance(y, pd.DataFrame):
        print(f"   Converting DataFrame to Series...")
        y = y.iloc[:, 0]
        print(f"   ✅ Converted")

    # Check for manual override
    if params.get('problem_type'):
        problem_type = params['problem_type']
        print(f"\n✅ Manual override: {problem_type.upper()}")
        return {
            'problem_type': problem_type,
            'method': 'manual_override',
            'confidence': 1.0
        }

    # Auto-detect
    unique_count = y.nunique()
    total_count = len(y)

    print(f"\nAuto-detection Analysis:")
    print(f"   Unique values: {unique_count}")
    print(f"   Total samples: {total_count}")
    print(f"   Data type: {y.dtype}")

    # Strategy 1: Data type
    if y.dtype == 'object':
        print(f"   ↓ Data type is 'object' (strings) → Classification")
        problem_type = 'classification'
        confidence = 0.95
    elif y.dtype in ['int64', 'int32', 'int16', 'int8']:
        if unique_count <= 10:
            print(f"   ↓ Integer with ≤10 unique values → Classification")
            problem_type = 'classification'
            confidence = 0.8
        else:
            print(f"   ↓ Integer with >10 unique values → Regression")
            problem_type = 'regression'
            confidence = 0.7
    elif y.dtype in ['float64', 'float32', 'float16']:
        print(f"   ↓ Float type → Regression")
        problem_type = 'regression'
        confidence = 0.9
    else:
        # Fallback: check cardinality
        pct_unique = (unique_count / total_count) * 100
        if pct_unique < 1.0:
            problem_type = 'classification'
            confidence = 0.6
        else:
            problem_type = 'regression'
            confidence = 0.6

    print(f"\n✅ Detected: {problem_type.upper()}")
    print(f"✅ Confidence: {confidence*100:.0f}%")

    if confidence < 0.7:
        print(f"\n⚠️  Low confidence - consider manual specification in params")

    print(f"{'='*80}\n")

    return {
        'problem_type': problem_type,
        'method': 'auto_detection',
        'confidence': confidence
    }


# ============================================================================
# GAP 5 FIX: USE REAL TARGET FOR FEATURE IMPORTANCE
# CRITICAL: Return DataFrame for CSV, not dict!
# ============================================================================

def calculate_feature_importance_with_real_target(
        X_train: pd.DataFrame,
        y_train: pd.DataFrame,
        problem_type_result: Dict[str, Any],
        params: Dict[str, Any]
) -> Tuple[pd.DataFrame, Dict[str, Any]]:
    """
    Calculate feature importance using REAL target (Gap 5 Fix).

    CRITICAL FIX: Returns DataFrame (not dict) as first output for CSV saving!

    Args:
        X_train: Training features
        y_train: REAL training target (DataFrame)
        problem_type_result: Dict from detect_problem_type with 'problem_type' key
        params: Configuration

    Returns:
        (importance_dataframe, importance_config)
        - importance_dataframe: DataFrame with rank, feature, importance (for CSV)
        - importance_config: Dict with metadata
    """
    print(f"\n{'='*80}")
    print(f"🏆 FEATURE IMPORTANCE WITH REAL TARGET (Gap 5 Fix)")
    print(f"{'='*80}")

    # Extract problem_type from dict (not bracket syntax!)
    problem_type = problem_type_result["problem_type"]

    # Convert DataFrame to Series if needed
    if isinstance(y_train, pd.DataFrame):
        y_train = y_train.iloc[:, 0]

    method = params.get('importance_method', 'tree')

    print(f"\nImportance Calculation:")
    print(f"   Method: {method}")
    print(f"   Features: {X_train.shape[1]}")
    print(f"   Samples: {len(X_train)}")
    print(f"   Target type: {problem_type}")
    print(f"   Using REAL target data (NOT fake random!)")

    # Validate target
    print(f"\n   Target Statistics:")
    print(f"      Unique values: {y_train.nunique()}")
    print(f"      Min: {y_train.min()}")
    print(f"      Max: {y_train.max()}")

    # Create appropriate model
    if problem_type == 'classification':
        model = RandomForestClassifier(
            n_estimators=50,
            random_state=42,
            n_jobs=-1,
            max_depth=10
        )
        print(f"\n   Model: RandomForestClassifier")
    else:
        model = RandomForestRegressor(
            n_estimators=50,
            random_state=42,
            n_jobs=-1,
            max_depth=10
        )
        print(f"\n   Model: RandomForestRegressor")

    # Fit model on REAL target
    print(f"\n   Fitting model on REAL target...")
    model.fit(X_train, y_train)
    print(f"   ✅ Model fitted")

    # Calculate importance
    if method == 'tree':
        importances = model.feature_importances_
    else:
        # Permutation importance
        print(f"\n   Calculating permutation importance (slower but more reliable)...")
        perm_importance = permutation_importance(
            model, X_train, y_train,
            n_repeats=5,
            random_state=42
        )
        importances = perm_importance.importances_mean

    # Create importance dictionary
    importance_dict = dict(zip(X_train.columns, importances))

    # Normalize to 0-100%
    total_imp = sum(importances)
    if total_imp > 0:
        importance_dict = {
            name: (imp / total_imp) * 100
            for name, imp in importance_dict.items()
        }

    # Sort by importance
    importance_dict = dict(sorted(
        importance_dict.items(),
        key=lambda x: -x[1]
    ))

    print(f"\n   Top 10 Important Features (based on REAL target):")
    for i, (feat, imp) in enumerate(list(importance_dict.items())[:10], 1):
        bar = "█" * int(imp / 5)
        print(f"      {i:2d}. {feat:30s} {imp:6.2f}% {bar}")

    # !!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!
    # CRITICAL FIX: Convert dict to DataFrame for CSV saving
    # !!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!
    importance_df = pd.DataFrame([
        {"feature": name, "importance": imp}
        for name, imp in importance_dict.items()
    ]).reset_index(drop=True)
    importance_df.insert(0, "rank", range(1, len(importance_df) + 1))

    print(f"{'='*80}\n")

    # Return DataFrame (not dict!) as first output
    return importance_df, {
        'method': method,
        'model': model,
        'features': X_train.columns.tolist(),
    }


def select_features_by_correlation(
        X_train: pd.DataFrame,
        params: Dict[str, Any]
) -> Tuple[pd.DataFrame, Dict[str, Any]]:
    """
    Select features by removing highly correlated features.

    Args:
        X_train: Training features (numeric only)
        params: Configuration

    Returns:
        (selected_features, selection_config)
    """
    print(f"\n🔗 CORRELATION-BASED FEATURE SELECTION")

    threshold = params.get('correlation_threshold', 0.9)

    print(f"   Threshold: {threshold}")

    # Calculate correlation
    correlation_matrix = X_train.corr().abs()

    # Find features to remove
    selected_cols = set(X_train.columns)

    for i in range(len(correlation_matrix.columns)):
        for j in range(i + 1, len(correlation_matrix.columns)):
            if correlation_matrix.iloc[i, j] > threshold:
                col_to_remove = correlation_matrix.columns[j]
                selected_cols.discard(col_to_remove)

    selected_cols = list(selected_cols)
    X_selected = X_train[selected_cols]

    removed = len(X_train.columns) - len(selected_cols)
    print(f"   Removed: {removed} features (corr > {threshold})")
    print(f"   Remaining: {len(selected_cols)} features")
    print(f"   ✅ Selection complete")

    return X_selected, {
        'method': 'correlation',
        'threshold': threshold,
        'removed_count': removed,
        'selected_features': selected_cols
    }


def select_top_features_by_importance(
        X_train: pd.DataFrame,
        feature_importance: pd.DataFrame,  # NOW RECEIVES DATAFRAME!
        params: Dict[str, Any]
) -> Tuple[pd.DataFrame, Dict[str, Any]]:
    """
    Select top N features by importance.

    Args:
        X_train: Training features
        feature_importance: DataFrame with importance scores (not dict!)
        params: Configuration

    Returns:
        (selected_features, selection_config)
    """
    print(f"\n⭐ IMPORTANCE-BASED FEATURE SELECTION")

    top_k = params.get('top_k', 20)

    # Get top K features from DataFrame
    sorted_features = feature_importance['feature'].head(top_k).tolist()
    X_selected = X_train[sorted_features]

    print(f"   Top K: {top_k}")
    print(f"   Selected {len(sorted_features)} features")
    print(f"\n   Selected Features:")
    for i, feat in enumerate(sorted_features, 1):
        imp = feature_importance[feature_importance['feature'] == feat]['importance'].values[0]
        print(f"      {i:2d}. {feat:30s} ({imp:6.2f}%)")

    print(f"\n   ✅ Selection complete")

    return X_selected, {
        'method': 'importance',
        'top_k': top_k,
        'selected_features': sorted_features
    }


def combine_selected_features(
        X_train_correlation: pd.DataFrame,
        X_train_importance: pd.DataFrame,
        params: Dict[str, Any]
) -> pd.DataFrame:
    """
    Combine features from multiple selection methods.

    Args:
        X_train_correlation: Features from correlation-based selection
        X_train_importance: Features from importance-based selection
        params: Configuration

    Returns:
        Combined selected features
    """
    print(f"\n🎁 COMBINING FEATURE SELECTION RESULTS")

    # Intersection of both methods (conservative)
    correlation_cols = set(X_train_correlation.columns)
    importance_cols = set(X_train_importance.columns)

    combined_cols = list(correlation_cols & importance_cols)

    print(f"   From correlation: {len(correlation_cols)} features")
    print(f"   From importance: {len(importance_cols)} features")
    print(f"   Combined (intersection): {len(combined_cols)} features")
    print(f"   ✅ Combination complete")

    return X_train_correlation[combined_cols]


def log_feature_selection_summary(
        X_train_final: pd.DataFrame,
        feature_importance: pd.DataFrame,  # NOW RECEIVES DATAFRAME!
        params: Dict[str, Any]
) -> pd.DataFrame:  # RETURN DATAFRAME
    """
    Log feature selection summary.

    CRITICAL: Returns DataFrame (not dict) for fs_summary output
    """
    summary_df = pd.DataFrame({
        'final_feature_count': [X_train_final.shape[1]],
        'total_features_evaluated': [len(feature_importance)]
    })

    log.info(f"\n🏆 Feature Selection Summary:")
    log.info(f"   Final feature count: {X_train_final.shape[1]}")
    log.info(f"   Top 5 features: {feature_importance['feature'].head(5).tolist()}")

    return summary_df


def create_pipeline(**kwargs) -> Pipeline:
    """
    Create feature selection pipeline.

    Flow:
    1. Detect problem type (Gap 2 Fix)
    2. Calculate importance with REAL target (Gap 5 Fix)
    3. Select features
    4. Combine results
    """
    return Pipeline(
        [
            # Problem Type Detection (Gap 2)
            node(
                func=detect_problem_type,
                inputs=["y_train", "params:feature_selection"],
                outputs="problem_type_result",
                name="detect_problem_type",
                tags="fs",
            ),
            # Feature Importance with Real Target (Gap 5) - FIXED: No bracket syntax!
            # CRITICAL: Now returns DataFrame as first output!
            node(
                func=calculate_feature_importance_with_real_target,
                inputs=["X_train_final", "y_train", "problem_type_result", "params:feature_selection"],
                outputs=["feature_importance", "importance_config"],  # feature_importance is now DataFrame
                name="calculate_feature_importance_with_real_target",
                tags="fs",
            ),
            # Correlation-based Selection
            node(
                func=select_features_by_correlation,
                inputs=["X_train_final", "params:feature_selection"],
                outputs=["X_train_correlation", "correlation_selection_config"],
                name="select_features_by_correlation",
                tags="fs",
            ),
            # Importance-based Selection (receives DataFrame now!)
            node(
                func=select_top_features_by_importance,
                inputs=["X_train_final", "feature_importance", "params:feature_selection"],  # feature_importance is DataFrame
                outputs=["X_train_importance", "importance_selection_config"],
                name="select_top_features_by_importance",
                tags="fs",
            ),
            # Combine Results
            node(
                func=combine_selected_features,
                inputs=["X_train_correlation", "X_train_importance", "params:feature_selection"],
                outputs="X_train_selected",
                name="combine_selected_features",
                tags="fs",
            ),
            # Summary (now returns DataFrame!)
            node(
                func=log_feature_selection_summary,
                inputs=["X_train_selected", "feature_importance", "params:feature_selection"],
                outputs="fs_summary",
                name="log_feature_selection_summary",
                tags="fs",
            ),
        ]
    )


if __name__ == "__main__":
    print("✅ Complete Final Phase 2 Feature Selection pipeline created!")
    print("   • Uses REAL target for importance (Gap 5 Fix)")
    print("   • Detects problem type robustly (Gap 2 Fix)")
    print("   • CRITICAL: Returns DataFrames for CSV saving (Dict→DataFrame fix)")