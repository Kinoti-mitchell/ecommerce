"""Product review sentiment with TextBlob (lightweight NLP)."""

from __future__ import annotations

import pandas as pd
from sklearn.metrics import accuracy_score, classification_report
from textblob import TextBlob


def blob_label(polarity: float, thresh: float = 0.05) -> str:
    if polarity > thresh:
        return "positive"
    if polarity < -thresh:
        return "negative"
    return "neutral"


def analyze_reviews(df: pd.DataFrame) -> tuple[pd.DataFrame, dict]:
    """
    Classify sentiment per row. Returns augmented dataframe and metrics
    when `true_sentiment` column exists.
    """
    out = df.copy()

    def score_text(t: str) -> float:
        if not isinstance(t, str) or not t.strip():
            return 0.0
        return float(TextBlob(t).sentiment.polarity)

    out["polarity"] = out["text"].map(score_text)
    out["sentiment"] = out["polarity"].map(blob_label)
    metrics: dict = {"n_reviews": len(out)}
    if "true_sentiment" in out.columns:
        mask = out["true_sentiment"].notna()
        metrics["accuracy_vs_synthetic_labels"] = float(
            accuracy_score(out.loc[mask, "true_sentiment"], out.loc[mask, "sentiment"])
        )
        metrics["classification_report"] = classification_report(
            out.loc[mask, "true_sentiment"],
            out.loc[mask, "sentiment"],
            output_dict=True,
            zero_division=0,
        )
    return out, metrics
