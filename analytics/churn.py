"""Customer churn prediction from behavioral features."""

from __future__ import annotations

from pathlib import Path

import joblib
import pandas as pd
from sklearn.ensemble import GradientBoostingClassifier
from sklearn.metrics import accuracy_score, classification_report, roc_auc_score
from sklearn.model_selection import train_test_split

ROOT = Path(__file__).resolve().parent.parent
MODEL_DIR = ROOT / "models"


def train_churn_model(df: pd.DataFrame) -> dict:
    MODEL_DIR.mkdir(parents=True, exist_ok=True)
    feature_cols = [
        "tenure_months",
        "monthly_spend",
        "sessions_per_month",
        "support_tickets",
    ]
    X = df[feature_cols]
    y = df["churned"]
    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.25, random_state=7, stratify=y
    )
    clf = GradientBoostingClassifier(random_state=7)
    clf.fit(X_train, y_train)
    y_pred = clf.predict(X_test)
    proba = clf.predict_proba(X_test)[:, 1]
    metrics = {
        "accuracy": float(accuracy_score(y_test, y_pred)),
        "roc_auc": float(roc_auc_score(y_test, proba)),
        "classification_report": classification_report(y_test, y_pred, output_dict=True),
    }
    joblib.dump(clf, MODEL_DIR / "churn_gb.joblib")
    joblib.dump(feature_cols, MODEL_DIR / "churn_feature_cols.joblib")
    return {"model": clf, "feature_cols": feature_cols, "metrics": metrics}


def churn_proba(df: pd.DataFrame) -> pd.Series:
    clf = joblib.load(MODEL_DIR / "churn_gb.joblib")
    cols = joblib.load(MODEL_DIR / "churn_feature_cols.joblib")
    return pd.Series(clf.predict_proba(df[cols])[:, 1], index=df.index)
