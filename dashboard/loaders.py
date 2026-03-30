"""Load persisted pipeline outputs for the Streamlit UI."""

from __future__ import annotations

import json
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parent.parent
OUTPUT = ROOT / "output"
DATA = ROOT / "data"


def load_metrics() -> dict:
    p = OUTPUT / "metrics.json"
    if not p.exists():
        return {}
    with open(p, encoding="utf-8") as f:
        return json.load(f)


def load_transactions_sample(n: int = 5000) -> pd.DataFrame:
    path = DATA / "transactions.csv"
    if not path.exists():
        return pd.DataFrame()
    return pd.read_csv(path, nrows=n)


def load_reviews_sample(n: int = 3000) -> pd.DataFrame:
    path = DATA / "reviews.json"
    if not path.exists():
        return pd.DataFrame()
    return pd.read_json(path, lines=True, nrows=n)


def load_rules() -> pd.DataFrame:
    p = OUTPUT / "association_rules.csv"
    if not p.exists():
        return pd.DataFrame()
    return pd.read_csv(p)


def load_churn_scores() -> pd.DataFrame:
    p = OUTPUT / "churn_scores.csv"
    if not p.exists():
        return pd.DataFrame()
    return pd.read_csv(p)


def load_sentiment_results() -> pd.DataFrame:
    p = OUTPUT / "sentiment_reviews.csv"
    if not p.exists():
        return pd.DataFrame()
    return pd.read_csv(p)
