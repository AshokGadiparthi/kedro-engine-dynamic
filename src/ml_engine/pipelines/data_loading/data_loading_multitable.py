"""
================================================================================
ENHANCED DATA LOADING MODULE - MULTI-TABLE SUPPORT
================================================================================

This module handles:
✅ Single-table datasets (CSV, Excel, JSON)
✅ Multi-table datasets with joins (SQL-like operations)
✅ Many-to-one relationships with aggregations
✅ Complex feature engineering from related tables
✅ Fully configuration-driven approach (no hardcoding)

Supported Patterns:
├─ Home Credit (7 related tables)
├─ Banking (accounts, transactions, balances)
├─ E-commerce (customers, orders, items, reviews)
├─ Healthcare (patients, visits, diagnoses, medications)
└─ Any tabular multi-table structure

Configuration-driven via:
├─ parameters.yml (data structure definition)
├─ catalog.yml (Kedro data catalog)
└─ Python configuration classes

================================================================================
"""

import pandas as pd
import numpy as np
from typing import Dict, List, Tuple, Any, Optional
from dataclasses import dataclass
from pathlib import Path
import logging
import json

logger = logging.getLogger(__name__)


# ════════════════════════════════════════════════════════════════════════════
# CONFIGURATION CLASSES (Declarative Data Structure)
# ════════════════════════════════════════════════════════════════════════════

@dataclass
class TableConfig:
    """Configuration for a single table in the dataset."""
    name: str                           # Table name (e.g., 'bureau')
    filepath: str                       # Path to CSV/Excel file
    id_column: str                      # Primary/Foreign key column
    parent_id_column: Optional[str] = None  # Parent table FK (for joins)
    is_main_table: bool = False         # Is this the main application table?


@dataclass
class AggregationConfig:
    """Configuration for aggregating many-to-one relationships."""
    table: str                          # Source table name
    group_by: str                       # Group by column
    features: Dict[str, str]            # {column: aggregation_function}
    # Example: {'AMT_CREDIT': 'max', 'DAYS_CREDIT': 'min', 'CNT_CREDIT': 'count'}
    prefix: str = ""                    # Prefix for aggregated columns


@dataclass
class JoinConfig:
    """Configuration for joining tables."""
    left_table: str                     # Left table name
    right_table: str                    # Right table name
    left_on: str                        # Left join column
    right_on: str                       # Right join column
    how: str = "left"                   # Join type (left, inner, outer, right)


@dataclass
class DatasetConfig:
    """Complete dataset configuration (replaces single data_path)."""
    mode: str                           # "single" or "multi"
    data_directory: str                 # Base directory for all files
    main_table: str                     # Main application table name
    target_column: str                  # Target variable column
    
    # For multi-table mode
    tables: Optional[List[TableConfig]] = None
    joins: Optional[List[JoinConfig]] = None
    aggregations: Optional[List[AggregationConfig]] = None
    
    # For single-table mode
    filepath: Optional[str] = None


# ════════════════════════════════════════════════════════════════════════════
# MULTI-TABLE DATA LOADER
# ════════════════════════════════════════════════════════════════════════════

class MultiTableDataLoader:
    """
    Load, join, and aggregate multiple related tables.
    
    Usage:
    ------
    config = DatasetConfig(
        mode='multi',
        data_directory='data/01_raw/home_credit/',
        main_table='application_train',
        target_column='TARGET',
        tables=[...],
        joins=[...],
        aggregations=[...]
    )
    
    loader = MultiTableDataLoader(config)
    data = loader.load_and_join()
    X, y = loader.separate_target()
    """
    
    def __init__(self, config: DatasetConfig, verbose: bool = True):
        self.config = config
        self.verbose = verbose
        self.tables: Dict[str, pd.DataFrame] = {}
        self.data: Optional[pd.DataFrame] = None

    def _log(self, msg: str, end: str = "\n"):
        """Log a message with optional end parameter."""
        if self.verbose:
            logger.info(msg)
            print(msg, end=end, flush=True)
    
    def load_all_tables(self) -> Dict[str, pd.DataFrame]:
        """
        Load all tables specified in configuration.
        
        Returns
        -------
        dict : {table_name: DataFrame}
        """
        self._log(f"\n{'='*80}")
        self._log("📂 LOADING TABLES")
        self._log(f"{'='*80}\n")
        
        for table_cfg in self.config.tables:
            filepath = Path(self.config.data_directory) / table_cfg.filepath
            
            self._log(f"Loading {table_cfg.name}... ", end="")
            
            try:
                if filepath.suffix == '.csv':
                    df = pd.read_csv(filepath)
                elif filepath.suffix in ['.xlsx', '.xls']:
                    df = pd.read_excel(filepath)
                elif filepath.suffix == '.parquet':
                    df = pd.read_parquet(filepath)
                else:
                    raise ValueError(f"Unsupported file type: {filepath.suffix}")
                
                self.tables[table_cfg.name] = df
                self._log(f"✅ ({df.shape[0]:,} rows × {df.shape[1]} cols)")
                
            except Exception as e:
                self._log(f"❌ Error: {e}")
                raise
        
        return self.tables
    
    def aggregate_tables(self) -> Dict[str, pd.DataFrame]:
        """
        Aggregate many-to-one relationships.
        
        Example: Bureau has many previous credits per applicant.
        Aggregate to get max credit, min days, etc. per applicant.
        
        Returns
        -------
        dict : {aggregated_table_name: DataFrame}
        """
        self._log(f"\n{'='*80}")
        self._log("🔄 AGGREGATING MANY-TO-ONE RELATIONSHIPS")
        self._log(f"{'='*80}\n")
        
        aggregated = {}
        
        for agg_cfg in self.config.aggregations:
            self._log(f"Aggregating {agg_cfg.table}...")
            
            source_table = self.tables[agg_cfg.table]
            
            # Group and aggregate
            agg_df = source_table.groupby(agg_cfg.group_by).agg(agg_cfg.features)
            
            # Flatten column names
            agg_df.columns = [f"{agg_cfg.prefix}{col}" if agg_cfg.prefix else col 
                             for col in agg_df.columns]
            
            agg_df = agg_df.reset_index()
            
            self._log(f"  ✅ Aggregated from {len(source_table):,} to {len(agg_df):,} rows")
            self._log(f"     Features created: {len(agg_cfg.features)}")
            
            aggregated[agg_cfg.table] = agg_df
        
        # Update tables with aggregated versions
        self.tables.update(aggregated)
        return aggregated
    
    def join_tables(self) -> pd.DataFrame:
        """
        Join all tables according to join configuration.
        
        Example:
        --------
        Main table: application (SK_ID_CURR)
            ← bureau_agg (SK_ID_CURR)
            ← pos_agg (SK_ID_CURR)
            ← credit_card_agg (SK_ID_CURR)
            ← previous_app_agg (SK_ID_CURR)
        
        Returns
        -------
        pd.DataFrame : Joined feature matrix
        """
        self._log(f"\n{'='*80}")
        self._log("🔗 JOINING TABLES")
        self._log(f"{'='*80}\n")
        
        # Start with main table
        main_table_name = self.config.main_table
        result = self.tables[main_table_name].copy()
        
        self._log(f"Starting with {main_table_name}: {result.shape}")
        
        # Apply joins
        for join_cfg in self.config.joins:
            left_table = self.tables[join_cfg.left_table]
            right_table = self.tables[join_cfg.right_table]
            
            self._log(f"\nJoining {join_cfg.left_table} ← {join_cfg.right_table}")
            self._log(f"  Type: {join_cfg.how}")
            self._log(f"  On: {join_cfg.left_table}.{join_cfg.left_on} = {join_cfg.right_table}.{join_cfg.right_on}")
            
            # Perform join
            result = result.merge(
                right_table,
                left_on=join_cfg.left_on,
                right_on=join_cfg.right_on,
                how=join_cfg.how,
                suffixes=('', f'_{join_cfg.right_table}')
            )
            
            self._log(f"  Result: {result.shape[0]:,} rows × {result.shape[1]} cols")
        
        self.data = result
        return result
    
    def load_and_join(self) -> pd.DataFrame:
        """
        Execute complete pipeline: load → aggregate → join.
        
        Returns
        -------
        pd.DataFrame : Fully joined feature matrix
        """
        # Load all tables
        self.load_all_tables()
        
        # Aggregate if needed
        if self.config.aggregations:
            self.aggregate_tables()
        
        # Join all tables
        if self.config.joins:
            self.join_tables()
        else:
            # No joins specified, return main table
            self.data = self.tables[self.config.main_table].copy()
        
        self._log(f"\n{'='*80}")
        self._log("✅ DATA LOADING COMPLETE")
        self._log(f"{'='*80}")
        self._log(f"Final shape: {self.data.shape[0]:,} rows × {self.data.shape[1]} columns")
        
        return self.data
    
    def separate_target(self) -> Tuple[pd.DataFrame, pd.Series]:
        """
        Separate features from target variable.
        
        Returns
        -------
        X : pd.DataFrame - Features
        y : pd.Series - Target variable
        """
        if self.data is None:
            raise ValueError("Must call load_and_join() first")
        
        if self.config.target_column not in self.data.columns:
            raise ValueError(f"Target column '{self.config.target_column}' not found")
        
        X = self.data.drop(columns=[self.config.target_column])
        y = self.data[self.config.target_column]
        
        return X, y
    
    def get_data_summary(self) -> Dict[str, Any]:
        """Get summary statistics of loaded data."""
        if self.data is None:
            raise ValueError("Must call load_and_join() first")
        
        return {
            'shape': self.data.shape,
            'columns': self.data.columns.tolist(),
            'missing_values': self.data.isnull().sum().to_dict(),
            'dtypes': self.data.dtypes.to_dict(),
            'target_distribution': self.data[self.config.target_column].value_counts().to_dict()
        }


# ════════════════════════════════════════════════════════════════════════════
# CONFIGURATION LOADING FROM YAML
# ════════════════════════════════════════════════════════════════════════════

def load_dataset_config_from_yaml(params: Dict[str, Any]) -> DatasetConfig:
    """
    Load DatasetConfig from parameters dictionary (from parameters.yml).
    
    Parameters
    ----------
    params : dict
        Dictionary with 'data_loading' key containing configuration
    
    Returns
    -------
    DatasetConfig
    """
    data_cfg = params.get('data_loading', {})
    
    if data_cfg.get('mode') == 'multi':
        # Multi-table mode
        tables_cfg = data_cfg.get('tables', [])
        tables = [
            TableConfig(
                name=t['name'],
                filepath=t['filepath'],
                id_column=t['id_column'],
                parent_id_column=t.get('parent_id_column'),
                is_main_table=t.get('is_main_table', False)
            )
            for t in tables_cfg
        ]
        
        joins_cfg = data_cfg.get('joins', [])
        joins = [
            JoinConfig(
                left_table=j['left_table'],
                right_table=j['right_table'],
                left_on=j['left_on'],
                right_on=j['right_on'],
                how=j.get('how', 'left')
            )
            for j in joins_cfg
        ]
        
        agg_cfg = data_cfg.get('aggregations', [])
        aggregations = [
            AggregationConfig(
                table=a['table'],
                group_by=a['group_by'],
                features=a['features'],
                prefix=a.get('prefix', '')
            )
            for a in agg_cfg
        ]
        
        return DatasetConfig(
            mode='multi',
            data_directory=data_cfg.get('data_directory'),
            main_table=data_cfg.get('main_table'),
            target_column=data_cfg.get('target_column'),
            tables=tables,
            joins=joins,
            aggregations=aggregations
        )
    else:
        # Single-table mode (backward compatible)
        return DatasetConfig(
            mode='single',
            data_directory=data_cfg.get('data_directory', 'data/01_raw/'),
            main_table='main',
            target_column=data_cfg.get('target_column'),
            filepath=data_cfg.get('filepath')
        )


# ════════════════════════════════════════════════════════════════════════════
# BACKWARD COMPATIBLE FUNCTIONS (Keep existing pipeline working)
# ════════════════════════════════════════════════════════════════════════════

def load_raw_data(filepath: str) -> pd.DataFrame:
    """
    ORIGINAL FUNCTION - Single table loading (backward compatible).
    
    Kept for compatibility with existing pipelines using single-table data.
    """
    print(f"📂 Loading raw data from: {filepath}")
    
    if filepath.endswith('.csv'):
        data = pd.read_csv(filepath)
    elif filepath.endswith('.xlsx') or filepath.endswith('.xls'):
        data = pd.read_excel(filepath)
    else:
        raise ValueError(f"Unsupported file type: {filepath}")
    
    print(f"✅ Loaded: {data.shape[0]} samples, {data.shape[1]} features")
    return data


def load_multi_table_data(config: DatasetConfig) -> pd.DataFrame:
    """
    NEW FUNCTION - Multi-table loading with joins and aggregations.
    
    Used for complex datasets like Home Credit.
    """
    loader = MultiTableDataLoader(config)
    return loader.load_and_join()


def load_data_with_config(params: Dict[str, Any]) -> Tuple[pd.DataFrame, pd.Series]:
    """
    Universal load function that detects mode and loads accordingly.
    
    Parameters
    ----------
    params : dict
        Configuration dictionary from parameters.yml
    
    Returns
    -------
    X : pd.DataFrame - Features
    y : pd.Series - Target
    """
    config = load_dataset_config_from_yaml(params)
    
    if config.mode == 'single':
        # Single-table mode
        data = load_raw_data(config.filepath)
    else:
        # Multi-table mode
        loader = MultiTableDataLoader(config)
        data = loader.load_and_join()
    
    # Separate target
    if config.target_column not in data.columns:
        raise ValueError(f"Target column '{config.target_column}' not found")
    
    X = data.drop(columns=[config.target_column])
    y = data[config.target_column]
    
    return X, y


# ════════════════════════════════════════════════════════════════════════════
# UTILITY FUNCTIONS
# ════════════════════════════════════════════════════════════════════════════

def print_table_schema(tables: Dict[str, pd.DataFrame]):
    """Print schema information for all loaded tables."""
    print("\n" + "="*80)
    print("📋 TABLE SCHEMA INFORMATION")
    print("="*80 + "\n")
    
    for table_name, df in tables.items():
        print(f"\n{table_name}:")
        print(f"  Shape: {df.shape[0]:,} rows × {df.shape[1]} columns")
        print(f"  Columns: {', '.join(df.columns[:10])}")
        if len(df.columns) > 10:
            print(f"           ... ({len(df.columns) - 10} more)")
        print(f"  Memory: {df.memory_usage(deep=True).sum() / 1024**2:.1f} MB")


def print_aggregation_summary(agg_results: Dict[str, pd.DataFrame]):
    """Print summary of aggregation results."""
    print("\n" + "="*80)
    print("📊 AGGREGATION SUMMARY")
    print("="*80 + "\n")
    
    for table_name, df in agg_results.items():
        print(f"{table_name}:")
        print(f"  Rows after aggregation: {len(df):,}")
        print(f"  New columns: {len(df.columns)}")


if __name__ == "__main__":
    print("✅ Multi-table data loader module ready!")
    print("   Use MultiTableDataLoader for complex datasets")
    print("   Use load_raw_data for single tables")
