"""
UNIFIED DATA LOADING - SUPPORTS BOTH SINGLE AND MULTI-TABLE DATASETS
====================================================================

✅ 100% GENERIC - NO HARDCODING
✅ BOTH MODES - Single-table AND multi-table
✅ CONFIGURATION-DRIVEN - Everything in parameters.yml
✅ BACKWARD COMPATIBLE - Existing code works unchanged
✅ SEAMLESS INTEGRATION - Works with pipeline_registry.py

This module provides a unified interface for loading data:
- Single CSV/Excel files (original mode)
- Multiple related tables with joins and aggregations (new mode)

Configuration in parameters.yml controls the mode:
  data_loading:
    mode: "single"  # or "multi"
    filepath: "data.csv"  # for single mode
    # OR
    tables: [...]  # for multi mode
    joins: [...]
    aggregations: [...]

NO BREAKING CHANGES - Phases 2-6 work with both modes!
"""

import pandas as pd
import numpy as np
from sklearn.model_selection import train_test_split
from typing import Tuple, Dict, Any, Optional
import logging
from kedro.pipeline import Pipeline, node
try:
    from .data_loading_multitable import (
        MultiTableDataLoader,
        DatasetConfig,
        TableConfig,
        AggregationConfig,
        JoinConfig
    )
    MULTI_TABLE_AVAILABLE = True
    print("✅ Multi-table loader imported successfully")
except Exception as e:
    MULTI_TABLE_AVAILABLE = False
    print(f"❌ Multi-table loader import failed: {e}")

log = logging.getLogger(__name__)
# ════════════════════════════════════════════════════════════════════════════
# ORIGINAL FUNCTIONS (BACKWARD COMPATIBLE)
# ════════════════════════════════════════════════════════════════════════════

def load_raw_data(filepath: str) -> pd.DataFrame:
    """
    Load raw data from single CSV/Excel file.

    Args:
        filepath: Path to data file

    Returns:
        DataFrame
    """
    log.info(f"📂 Loading raw data from: {filepath}")

    if filepath.endswith('.csv'):
        data = pd.read_csv(filepath)
    elif filepath.endswith('.xlsx') or filepath.endswith('.xls'):
        data = pd.read_excel(filepath)
    else:
        raise ValueError(f"Unsupported file type: {filepath}")

    log.info(f"✅ Loaded: {data.shape[0]} samples, {data.shape[1]} features")
    return data


def separate_target(
        raw_data: pd.DataFrame,
        target_column: str = 'target'
) -> Tuple[pd.DataFrame, pd.Series]:
    """
    Separate features from target variable.

    Args:
        raw_data: Raw DataFrame
        target_column: Name of target column

    Returns:
        Tuple of (features DataFrame, target Series)
    """
    log.info(f"🎯 Separating target column: {target_column}")

    if target_column not in raw_data.columns:
        raise ValueError(f"Target column '{target_column}' not found in data")

    X = raw_data.drop(columns=[target_column])
    y = raw_data[target_column]

    log.info(f"✅ Features: {X.shape} | Target: {y.shape}")
    return X, y


def split_data(
        X: pd.DataFrame,
        y: pd.Series,
        test_size: float = 0.2,
        random_state: int = 42,
        stratify: bool = True
) -> Tuple[pd.DataFrame, pd.DataFrame, pd.Series, pd.Series]:
    """
    Split data into train and test sets.

    Args:
        X: Features DataFrame
        y: Target Series
        test_size: Test set fraction
        random_state: Random seed
        stratify: Whether to stratify by target

    Returns:
        (X_train, X_test, y_train, y_test)
    """
    log.info(f"📊 Splitting data (test_size={test_size})")

    stratify_arg = y if stratify else None

    X_train, X_test, y_train, y_test = train_test_split(
        X, y,
        test_size=test_size,
        random_state=random_state,
        stratify=stratify_arg
    )

    log.info(f"✅ Train: {X_train.shape} | Test: {X_test.shape}")
    return X_train, X_test, y_train, y_test


# ════════════════════════════════════════════════════════════════════════════
# NEW UNIFIED FUNCTION - AUTO-DETECTS MODE
# ════════════════════════════════════════════════════════════════════════════

def load_data_auto(
        data_cfg: Dict[str, Any]  # ✅ Parameter is data_cfg
) -> Tuple[pd.DataFrame, pd.DataFrame, pd.Series, pd.Series]:
    """
    AUTO-DETECTING DATA LOADER

    Automatically detects and routes to appropriate loader:
    - Single-table mode: loads CSV/Excel, returns (X_train, X_test, y_train, y_test)
    - Multi-table mode: loads multiple tables, joins, aggregates, returns same format
    """

    # ✅ Use data_cfg directly (no nested access!)
    mode = data_cfg.get('mode', 'single')

    log.info(f"\n{'='*80}")
    log.info(f"📊 DATA LOADING - MODE: {mode.upper()}")
    log.info(f"{'='*80}\n")

    if mode == 'multi':
        # Multi-table mode
        if not MULTI_TABLE_AVAILABLE:
            raise RuntimeError("Multi-table loader not available!")

        log.info("🔗 Multi-Table Mode Activated")
        data = _load_multi_table(data_cfg)
    else:
        # Single-table mode (default)
        log.info("📂 Single-Table Mode Activated")
        data = _load_single_table(data_cfg)

    # Separate target and split
    target_column = data_cfg.get('target_column', 'target')
    X, y = separate_target(data, target_column)

    test_size = data_cfg.get('test_size', 0.2)
    random_state = data_cfg.get('random_state', 42)
    stratify = data_cfg.get('stratify', True)

    X_train, X_test, y_train, y_test = split_data(
        X, y,
        test_size=test_size,
        random_state=random_state,
        stratify=stratify
    )

    log.info(f"\n{'='*80}")
    log.info(f"✅ DATA LOADING COMPLETE")
    log.info(f"   Train: {X_train.shape} | Test: {X_test.shape}")
    log.info(f"{'='*80}\n")

    return X_train, X_test, y_train, y_test


# ════════════════════════════════════════════════════════════════════════════
# INTERNAL FUNCTIONS
# ════════════════════════════════════════════════════════════════════════════

def _load_single_table(data_cfg: Dict[str, Any]) -> pd.DataFrame:
    """Load single CSV/Excel file."""
    filepath = data_cfg.get('filepath')
    if not filepath:
        raise ValueError("filepath required for single-table mode")

    return load_raw_data(filepath)


def _load_multi_table(data_cfg: Dict[str, Any]) -> pd.DataFrame:
    """Load multiple tables with joins and aggregations."""

    # Build configuration objects
    data_directory = data_cfg.get('data_directory', 'data/01_raw/')
    main_table = data_cfg.get('main_table')
    target_column = data_cfg.get('target_column', 'target')

    # Parse tables
    tables = []
    for t_cfg in data_cfg.get('tables', []):
        tables.append(TableConfig(
            name=t_cfg['name'],
            filepath=t_cfg['filepath'],
            id_column=t_cfg['id_column'],
            parent_id_column=t_cfg.get('parent_id_column'),
            is_main_table=(t_cfg['name'] == main_table)
        ))

    # Parse aggregations
    aggregations = []
    for a_cfg in data_cfg.get('aggregations', []):
        aggregations.append(AggregationConfig(
            table=a_cfg['table'],
            group_by=a_cfg['group_by'],
            features=a_cfg['features'],
            prefix=a_cfg.get('prefix', '')
        ))

    # Parse joins
    joins = []
    for j_cfg in data_cfg.get('joins', []):
        joins.append(JoinConfig(
            left_table=j_cfg['left_table'],
            right_table=j_cfg['right_table'],
            left_on=j_cfg['left_on'],
            right_on=j_cfg['right_on'],
            how=j_cfg.get('how', 'left')
        ))

    # Create config
    config = DatasetConfig(
        mode='multi',
        data_directory=data_directory,
        main_table=main_table,
        target_column=target_column,
        tables=tables,
        joins=joins,
        aggregations=aggregations
    )

    # Load data
    loader = MultiTableDataLoader(config, verbose=True)
    return loader.load_and_join()


# ════════════════════════════════════════════════════════════════════════════
# PIPELINE INTEGRATION (CRITICAL FOR pipeline_registry.py)
# ════════════════════════════════════════════════════════════════════════════

def create_pipeline() -> Pipeline:
    """
    Create data loading pipeline.

    ✅ Works with existing pipeline_registry.py
    ✅ Supports both single-table and multi-table modes
    ✅ Configuration-driven (reads from parameters.yml)
    ✅ No breaking changes

    Output nodes:
    - X_train_raw
    - X_test_raw
    - y_train_raw
    - y_test_raw

    These same output names work for both modes!
    Phases 2-6 work identically with both modes.
    """
    return Pipeline([
        node(
            func=load_data_auto,
            inputs="params:data_loading",
            outputs=[
                "X_train_raw",
                "X_test_raw",
                "y_train_raw",
                "y_test_raw"
            ],
            name="load_data_node"
        )
    ])


if __name__ == "__main__":
    print("\n" + "="*80)
    print("✅ UNIFIED DATA LOADING MODULE")
    print("="*80)
    print("\n✨ Features:")
    print("  ✅ Single-table mode (CSV/Excel files)")
    print("  ✅ Multi-table mode (joins + aggregations)")
    print("  ✅ Configuration-driven (parameters.yml)")
    print("  ✅ Backward compatible (existing code works)")
    print("  ✅ Seamless integration (works with pipeline_registry.py)")
    print("\n🎯 Mode auto-detection:")
    print("  - mode: 'single' → CSV/Excel file loading")
    print("  - mode: 'multi' → Multi-table loading with joins")
    print("\n💡 Everything configurable in parameters.yml\n")