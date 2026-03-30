import pandas as pd

from utils.mapreduce_helpers import fraud_map_chunk, fraud_reduce_user, run_fraud_mapreduce


def test_fraud_reduce_user_sums_partials():
    out = fraud_reduce_user(
        1,
        [
            {"count": 2, "sum_amount": 10.0, "unusual_loc": 0, "high_amt": 1},
            {"count": 1, "sum_amount": 5.0, "unusual_loc": 1, "high_amt": 0},
        ],
    )
    assert out["txn_count"] == 3
    assert out["total_amount"] == 15.0
    assert out["rows_missing_location"] == 1
    assert out["high_amount_txns"] == 1


def test_run_fraud_mapreduce_returns_dataframe():
    df = pd.DataFrame(
        {
            "user_id": [1, 1, 2],
            "amount": [100.0, 200.0, 50.0],
            "location_id": [1, 1, 2],
        }
    )
    r = run_fraud_mapreduce(df, n_chunks=2)
    assert len(r) == 2
    assert "txn_count" in r.columns
