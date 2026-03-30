"""Score a single hypothetical transaction for demos (uses saved models + user history)."""

from __future__ import annotations

from typing import Any

import numpy as np
import pandas as pd

from analytics.anomalies import load_anomaly_artifacts
from analytics.fraud import engineer_fraud_features, load_fraud_artifacts
from utils.cleaning import clean_transactions


def score_hypothetical_transaction(
    user_id: int,
    amount: float,
    location_id: float,
    device_id: int,
    context_tx: pd.DataFrame,
) -> tuple[dict[str, Any] | None, str | None]:
    """
    Append one row after that user's history in ``context_tx``, engineer features,
    return fraud probability and anomaly score. ``context_tx`` must be raw-like
    (same columns as ``transactions.csv``).
    """
    hist = context_tx[context_tx["user_id"] == int(user_id)].copy()
    if hist.empty:
        return None, (
            f"No rows for user **{user_id}** in the current chart sample. "
            "Raise **Fraud chart sample size** in the sidebar or pick another user."
        )

    hist = hist.copy()
    hist["timestamp"] = pd.to_datetime(hist["timestamp"])
    ts_max = hist["timestamp"].max()
    new_ts = ts_max + pd.Timedelta(minutes=1)
    new_row = pd.DataFrame(
        [
            {
                "user_id": int(user_id),
                "amount": float(amount),
                "location_id": float(location_id),
                "device_id": int(device_id),
                "timestamp": new_ts,
                "is_fraud": 0,
            }
        ]
    )
    combined = pd.concat([hist, new_row], ignore_index=True)
    combined = clean_transactions(combined)
    feat = engineer_fraud_features(combined)
    last = feat.iloc[[-1]]

    clf, cols = load_fraud_artifacts("fraud_rf")
    fraud_p = float(clf.predict_proba(last[cols].fillna(0))[:, 1][0])

    anom: float | None
    try:
        clf_if, cols_if = load_anomaly_artifacts()
        X = last[cols_if].fillna(0).astype(np.float64)
        anom = float(-clf_if.score_samples(X)[0])
    except Exception:
        anom = None

    out = {
        "fraud_proba": fraud_p,
        "anomaly_score": anom,
        "unusual_location": int(last["unusual_location"].iloc[0]),
        "high_spend": int(last["high_spend"].iloc[0]),
        "new_device": int(last["new_device"].iloc[0]),
    }
    return out, None
