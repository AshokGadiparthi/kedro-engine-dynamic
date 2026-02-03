"""Encoding utility functions for categorical variables."""

from sklearn.preprocessing import OneHotEncoder, LabelEncoder
import pandas as pd
import logging

log = logging.getLogger(__name__)


class CategoricalEncoder:
    """Handles categorical encoding."""

    @staticmethod
    def one_hot_encode(data: pd.DataFrame, columns: list) -> pd.DataFrame:
        """Apply OneHotEncoding to specified columns."""
        encoder = OneHotEncoder(sparse=False, handle_unknown='ignore')
        encoded = encoder.fit_transform(data[columns])

        new_cols = encoder.get_feature_names_out(columns)
        encoded_df = pd.DataFrame(encoded, columns=new_cols)

        # Combine with non-encoded columns
        other_cols = [col for col in data.columns if col not in columns]
        result = pd.concat([data[other_cols], encoded_df], axis=1)

        return result

    @staticmethod
    def label_encode(data: pd.DataFrame, columns: list) -> pd.DataFrame:
        """Apply LabelEncoding to specified columns."""
        result = data.copy()

        for col in columns:
            encoder = LabelEncoder()
            result[col] = encoder.fit_transform(result[col].astype(str))

        return result