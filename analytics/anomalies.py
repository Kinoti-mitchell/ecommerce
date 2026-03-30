"""
Unsupervised transaction anomaly detection.

Uses an Isolation Forest on engineered **behavior** features only — the model is
**not** trained on `is_fraud`. It flags rare combinations (amount, location change,
device, spend spike) that may indicate issues not captured by explicit rules.

For comparison, the supervised fraud model in `analytics/fraud.py` optimizes for
the fraud label; this module surfaces **novelty / rarity** in feature space.
"""

from __future__ import annotations

from typing import Any

import joblib
import numpy as np
import pandas as pd
from sklearn.ensemble import IsolationForest

import config
from analytics.fraud import engineer_fraud_features

MODEL_DIR = config.MODELS_DIR
OUTPUT_DIR = config.OUTPUT_DIR

# Same signals as fraud features, but IF does not use `is_fraud` during fit.
DEFAULT_FEATURE_COLS = ["amount", "unusual_location", "high_spend", "new_device"]


def fit_transaction_anomalies(
    tx_clean: pd.DataFrame,
    *,
    feature_cols: list[str] | None = None,
    contamination: float = 0.03,
    n_estimators: int = 120,
    random_state: int = 42,
) -> dict[str, Any]:
    """
    Fit IsolationForest on cleaned transactions (no label used for training).

    Returns dict with fitted model, feature columns, scored frame, and summary stats.
    """
    feature_cols = feature_cols or DEFAULT_FEATURE_COLS
    MODEL_DIR.mkdir(parents=True, exist_ok=True)

    feat_df = engineer_fraud_features(tx_clean).reset_index(drop=True)
    X = feat_df[feature_cols].fillna(0).astype(np.float64)

    clf = IsolationForest(
        n_estimators=n_estimators,
        contamination=contamination,
        random_state=random_state,
        n_jobs=1,
    )
    clf.fit(X)
    # sklearn: lower score_samples = more anomalous; flip so "higher = more suspicious"
    raw_score = clf.score_samples(X)
    anomaly_score = -raw_score
    pred = clf.predict(X)

    out = feat_df.copy()
    out["anomaly_score"] = anomaly_score
    out["isolation_forest_outlier"] = pred == -1

    suf = "transaction_anomaly_if"
    joblib.dump(clf, MODEL_DIR / f"{suf}.joblib")
    joblib.dump(feature_cols, MODEL_DIR / f"{suf}_cols.joblib")

    overlap = None
    if "is_fraud" in out.columns and len(out) >= 100:
        top100 = out.loc[out["anomaly_score"].nlargest(100).index]
        overlap = float(top100["is_fraud"].mean())

    summary = {
        "n_rows": int(len(out)),
        "n_estimators": n_estimators,
        "contamination": contamination,
        "n_flagged_outliers": int((pred == -1).sum()),
        "feature_cols": feature_cols,
        "top_100_overlap_with_labeled_fraud": overlap,
        "mean_anomaly_score": float(anomaly_score.mean()),
        "std_anomaly_score": float(anomaly_score.std()),
    }
    return {
        "model": clf,
        "feature_cols": feature_cols,
        "scored": out,
        "summary": summary,
    }


def save_anomaly_outputs(result: dict[str, Any]) -> None:
    """Write scored transactions and a ranked top list for the dashboard."""
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    scored: pd.DataFrame = result["scored"]
    cols_out = [
        c
        for c in [
            "user_id",
            "amount",
            "location_id",
            "device_id",
            "timestamp",
            "unusual_location",
            "high_spend",
            "new_device",
            "anomaly_score",
            "isolation_forest_outlier",
            "is_fraud",
        ]
        if c in scored.columns
    ]
    scored[cols_out].to_csv(OUTPUT_DIR / "transaction_anomaly_scores.csv", index=False)

    top = scored.nlargest(500, "anomaly_score")[cols_out]
    top.to_csv(OUTPUT_DIR / "transaction_anomalies_top500.csv", index=False)


def load_anomaly_artifacts():
    clf = joblib.load(MODEL_DIR / "transaction_anomaly_if.joblib")
    cols = joblib.load(MODEL_DIR / "transaction_anomaly_if_cols.joblib")
    return clf, cols


def anomaly_scores_for_transactions(tx_clean: pd.DataFrame) -> np.ndarray:
    """Score new rows with the saved Isolation Forest (same features as training)."""
    clf, cols = load_anomaly_artifacts()
    feat_df = engineer_fraud_features(tx_clean)
    X = feat_df[cols].fillna(0).astype(np.float64)
    return -clf.score_samples(X)
