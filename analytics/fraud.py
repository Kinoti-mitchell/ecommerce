"""
Credit card fraud detection (classification).

Features engineered to mirror common rules + model-based scoring:
- unusual location vs user's typical locations
- high spend vs user's historical amounts
- new device (first time seeing device_id for user)
"""

from __future__ import annotations

import joblib
import numpy as np
import pandas as pd
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import accuracy_score, classification_report, roc_auc_score
from sklearn.model_selection import train_test_split

import config

MODEL_DIR = config.MODELS_DIR


def engineer_fraud_features(df: pd.DataFrame) -> pd.DataFrame:
    """Add columns used by the classifier (expects cleaned transactions)."""
    out = df.sort_values(["user_id", "timestamp"]).copy()
    # User typical location (mode)
    def _mode_or_median(s: pd.Series):
        m = s.mode()
        if len(m):
            return m.iloc[0]
        return s.median()

    mode_loc = out.groupby("user_id")["location_id"].transform(_mode_or_median)
    mode_loc = mode_loc.fillna(out["location_id"].median())
    out["unusual_location"] = (out["location_id"] != mode_loc).astype(int)
    # Per-user amount percentile (vectorized). In production you'd use time-safe
    # features (e.g. rolling windows) to avoid leakage; this is fast for large n.
    user_p95 = out.groupby("user_id")["amount"].transform("quantile", q=0.95)
    global_p95 = out["amount"].quantile(0.95)
    user_p95 = user_p95.fillna(global_p95)
    out["high_spend"] = (out["amount"] > user_p95).astype(int)
    # First time this user uses this device_id in time order
    out["new_device"] = (
        out.groupby(["user_id", "device_id"]).cumcount().eq(0).astype(int)
    )
    return out


def train_fraud_model(
    df: pd.DataFrame,
    model_suffix: str = "",
    *,
    use_engineering: bool = True,
    feature_cols: list[str] | None = None,
) -> dict:
    MODEL_DIR.mkdir(parents=True, exist_ok=True)
    if use_engineering:
        feat_df = engineer_fraud_features(df)
        if feature_cols is None:
            feature_cols = ["amount", "unusual_location", "high_spend", "new_device"]
    else:
        # Weak baseline: no cleaning beyond coercing amount — shows value of features + ETL
        feat_df = df.copy()
        feat_df["amount"] = pd.to_numeric(feat_df["amount"], errors="coerce").fillna(0.0)
        feature_cols = feature_cols or ["amount"]
    X = feat_df[feature_cols].fillna(0)
    y = feat_df["is_fraud"]
    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.25, random_state=42, stratify=y
    )
    clf = RandomForestClassifier(
        n_estimators=80,
        max_depth=12,
        class_weight="balanced",
        random_state=42,
        n_jobs=1,
    )
    clf.fit(X_train, y_train)
    y_pred = clf.predict(X_test)
    proba = clf.predict_proba(X_test)[:, 1]
    metrics = {
        "accuracy": float(accuracy_score(y_test, y_pred)),
        "roc_auc": float(roc_auc_score(y_test, proba)),
        "classification_report": classification_report(y_test, y_pred, output_dict=True),
    }
    suf = model_suffix or "fraud_rf"
    joblib.dump(clf, MODEL_DIR / f"{suf}.joblib")
    joblib.dump(feature_cols, MODEL_DIR / f"{suf}_feature_cols.joblib")
    return {"model": clf, "feature_cols": feature_cols, "metrics": metrics}


def load_fraud_artifacts(suffix: str = "fraud_rf"):
    clf = joblib.load(MODEL_DIR / f"{suffix}.joblib")
    cols = joblib.load(MODEL_DIR / f"{suffix}_feature_cols.joblib")
    return clf, cols


def fraud_proba(df: pd.DataFrame, clf=None, feature_cols: list[str] | None = None) -> np.ndarray:
    if clf is None:
        clf, feature_cols = load_fraud_artifacts()
    feat_df = engineer_fraud_features(df)
    X = feat_df[feature_cols].fillna(0)
    return clf.predict_proba(X)[:, 1]
