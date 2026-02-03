"""Scaling utility functions for feature engineering."""

from sklearn.preprocessing import StandardScaler, MinMaxScaler, RobustScaler
import pandas as pd
import logging

log = logging.getLogger(__name__)


class FeatureScaler:
    """Handles feature scaling."""

    @staticmethod
    def scale_standard(data: pd.DataFrame) -> pd.DataFrame:
        """StandardScaler with mean=0, std=1."""
        scaler = StandardScaler()
        scaled = scaler.fit_transform(data)
        return pd.DataFrame(scaled, columns=data.columns)

    @staticmethod
    def scale_minmax(data: pd.DataFrame) -> pd.DataFrame:
        """MinMaxScaler to range [0, 1]."""
        scaler = MinMaxScaler()
        scaled = scaler.fit_transform(data)
        return pd.DataFrame(scaled, columns=data.columns)

    @staticmethod
    def scale_robust(data: pd.DataFrame) -> pd.DataFrame:
        """RobustScaler using quartiles."""
        scaler = RobustScaler()
        scaled = scaler.fit_transform(data)
        return pd.DataFrame(scaled, columns=data.columns)