"""Imputation utility functions for missing values."""

from sklearn.impute import SimpleImputer, KNNImputer
import pandas as pd
import logging

log = logging.getLogger(__name__)


class MissingValueHandler:
    """Handles missing value imputation."""

    @staticmethod
    def impute_mean(data: pd.DataFrame) -> pd.DataFrame:
        """Impute missing values with mean."""
        imputer = SimpleImputer(strategy='mean')
        imputed = imputer.fit_transform(data)
        return pd.DataFrame(imputed, columns=data.columns)

    @staticmethod
    def impute_median(data: pd.DataFrame) -> pd.DataFrame:
        """Impute missing values with median."""
        imputer = SimpleImputer(strategy='median')
        imputed = imputer.fit_transform(data)
        return pd.DataFrame(imputed, columns=data.columns)

    @staticmethod
    def impute_knn(data: pd.DataFrame, n_neighbors: int = 5) -> pd.DataFrame:
        """Impute missing values using KNN."""
        imputer = KNNImputer(n_neighbors=n_neighbors)
        imputed = imputer.fit_transform(data)
        return pd.DataFrame(imputed, columns=data.columns)

    @staticmethod
    def impute_forward_fill(data: pd.DataFrame, limit: int = 3) -> pd.DataFrame:
        """Forward fill missing values."""
        return data.fillna(method='ffill', limit=limit)