import pandas as pd

from utils.cleaning import clean_transactions


def test_clean_transactions_fixes_negative_amount():
    df = pd.DataFrame(
        {
            "user_id": [1, 1],
            "amount": [10.0, -5.0],
            "location_id": [1, 1],
            "device_id": [1, 1],
            "timestamp": pd.date_range("2024-01-01", periods=2, freq="h"),
            "is_fraud": [0, 0],
        }
    )
    out = clean_transactions(df)
    assert (out["amount"] > 0).all()


def test_clean_transactions_fills_missing_location():
    df = pd.DataFrame(
        {
            "user_id": [1, 1, 1],
            "amount": [10.0, 20.0, 15.0],
            "location_id": [5.0, float("nan"), 5.0],
            "device_id": [1, 1, 1],
            "timestamp": pd.date_range("2024-01-01", periods=3, freq="h"),
            "is_fraud": [0, 0, 0],
        }
    )
    out = clean_transactions(df)
    assert out["location_id"].notna().all()
