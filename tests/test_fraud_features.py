import pandas as pd

from analytics.fraud import engineer_fraud_features
from utils.cleaning import clean_transactions


def _tiny_tx():
    df = pd.DataFrame(
        {
            "user_id": [1, 1, 1, 1],
            "amount": [10.0, 12.0, 500.0, 11.0],
            "location_id": [1, 1, 1, 2],
            "device_id": [10, 10, 11, 10],
            "timestamp": pd.date_range("2024-01-01", periods=4, freq="h"),
            "is_fraud": [0, 0, 0, 0],
        }
    )
    return clean_transactions(df)


def test_engineer_fraud_features_adds_columns():
    df = _tiny_tx()
    out = engineer_fraud_features(df)
    for c in ("unusual_location", "high_spend", "new_device"):
        assert c in out.columns
