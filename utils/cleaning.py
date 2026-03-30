"""
Data cleaning for messy e-commerce feeds.

Real Hadoop/Spark pipelines often run cleaning as:
- Batch: Spark SQL / DataFrame transforms over partitioned Parquet on HDFS.
- Or MapReduce jobs that emit cleaned records in the reduce phase.

Improving models: imputation and outlier handling reduce noise so classifiers
see more consistent feature distributions.
"""

from __future__ import annotations

import numpy as np
import pandas as pd


def clean_transactions(df: pd.DataFrame) -> pd.DataFrame:
    out = df.copy()
    # Missing location: fill with user's mode if available, else global median
    loc_med = int(out["location_id"].median(skipna=True))
    out["location_id"] = out.groupby("user_id")["location_id"].transform(
        lambda s: s.fillna(s.mode().iloc[0] if len(s.mode()) else loc_med)
    )
    out["location_id"] = out["location_id"].fillna(loc_med)
    # Invalid amounts
    out["amount"] = out["amount"].abs()
    out.loc[out["amount"] <= 0, "amount"] = out["amount"].median()
    return out


def clean_reviews(df: pd.DataFrame) -> pd.DataFrame:
    out = df.copy()
    out["text"] = out["text"].fillna("").astype(str)
    out["text"] = out["text"].str.replace("###CORRUPT###", "", regex=False).str.strip()
    out.loc[out["text"] == "", "text"] = "neutral review placeholder"
    return out


def clean_baskets(df: pd.DataFrame) -> pd.DataFrame:
    out = df.dropna(subset=["product_id"]).copy()
    out["product_id"] = out["product_id"].astype(str).str.upper().str.strip()
    return out[out["product_id"].str.len() > 0]


def clean_churn(df: pd.DataFrame) -> pd.DataFrame:
    out = df.copy()
    med = out["monthly_spend"].median()
    out["monthly_spend"] = out["monthly_spend"].fillna(med)
    return out


def clean_ratings(df: pd.DataFrame) -> pd.DataFrame:
    out = df.copy()
    out = out.dropna(subset=["rating"])
    out["rating"] = out["rating"].clip(1, 5).astype(int)
    return out
