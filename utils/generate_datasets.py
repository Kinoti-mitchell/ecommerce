"""
Synthetic e-commerce datasets for the simulated data lake (HDFS-style storage).

In production Hadoop:
- Files would live on HDFS as partitioned Parquet/ORC/Avro in a lakehouse.
- NameNode tracks block locations; DataNodes store replicated blocks (default 3x).
- Spark or MapReduce jobs read splits in parallel across the cluster.
"""

from __future__ import annotations

import json
import os
from pathlib import Path

import numpy as np
import pandas as pd

# Project root: parent of utils/
ROOT = Path(__file__).resolve().parent.parent
DATA_LAKE = ROOT / "data"


def _ensure_lake() -> Path:
    DATA_LAKE.mkdir(parents=True, exist_ok=True)
    return DATA_LAKE


def generate_transactions(n_rows: int = 55_000, seed: int = 42) -> pd.DataFrame:
    """
    Synthetic card transactions with latent fraud patterns.
    Ground-truth `is_fraud` is used for supervised learning evaluation.
    """
    rng = np.random.default_rng(seed)
    n_users = 8_000
    user_id = rng.integers(1, n_users + 1, size=n_rows)
    # "Home" location per user (simulate habitual geography)
    home_loc = rng.integers(1, 200, size=n_users + 1)
    location_id = home_loc[user_id].copy()
    # Some transactions away from home (higher fraud correlation in this toy model)
    away_mask = rng.random(n_rows) < 0.12
    location_id[away_mask] = rng.integers(1, 500, size=away_mask.sum())

    amount = rng.lognormal(mean=3.5, sigma=1.2, size=n_rows).clip(0.5, 50_000)
    # Fraud tends to be higher amount in this simulation
    fraud_base = rng.random(n_rows) < 0.03
    amount[fraud_base] *= rng.uniform(2.0, 8.0, size=fraud_base.sum())

    device_id = rng.integers(1, 50_000, size=n_rows)
    # New device: randomize device for subset (fraud signal)
    new_dev = rng.random(n_rows) < 0.08
    device_id[new_dev] = rng.integers(50_000, 200_000, size=new_dev.sum())

    ts = pd.date_range("2024-01-01", periods=n_rows, freq="min")
    ts = ts.to_series().sample(n_rows, replace=True, random_state=seed).values

    # Latent fraud score from features (interpretable toy rules)
    z_amount = (amount > np.percentile(amount, 97)).astype(int)
    unusual_loc = (location_id != home_loc[user_id]).astype(int)
    new_device_flag = new_dev.astype(int)
    fraud_prob = 0.08 * unusual_loc + 0.06 * z_amount + 0.05 * new_device_flag
    is_fraud = (rng.random(n_rows) < fraud_prob).astype(int)

    df = pd.DataFrame(
        {
            "user_id": user_id,
            "amount": np.round(amount, 2),
            "location_id": location_id,
            "device_id": device_id,
            "timestamp": ts,
            "is_fraud": is_fraud,
        }
    )
    # Data quality issues: missing / noisy
    miss = rng.choice(df.index, size=int(n_rows * 0.02), replace=False)
    df.loc[miss, "location_id"] = np.nan
    noise_idx = rng.choice(df.index, size=int(n_rows * 0.01), replace=False)
    df.loc[noise_idx, "amount"] = -df.loc[noise_idx, "amount"].abs()  # invalid negative

    return df.sample(frac=1.0, random_state=seed).reset_index(drop=True)


def generate_reviews(n_rows: int = 12_000, seed: int = 43) -> pd.DataFrame:
    rng = np.random.default_rng(seed)
    positive = [
        "Love this product, great quality and fast shipping!",
        "Excellent value, would buy again.",
        "Amazing experience, highly recommend to everyone.",
        "Five stars, works perfectly out of the box.",
        "Super happy with purchase, customer service was helpful.",
    ]
    negative = [
        "Terrible quality, broke after one day.",
        "Worst purchase ever, do not buy.",
        "Shipping was late and item was damaged.",
        "Not as described, very disappointed.",
        "Refund process was a nightmare.",
    ]
    neutral = [
        "It is okay, nothing special.",
        "Average product for the price.",
        "Does the job, could be better.",
    ]
    texts = []
    labels = []
    for _ in range(n_rows):
        r = rng.random()
        if r < 0.45:
            texts.append(rng.choice(positive))
            labels.append("positive")
        elif r < 0.75:
            texts.append(rng.choice(negative))
            labels.append("negative")
        else:
            texts.append(rng.choice(neutral))
            labels.append("neutral")
    df = pd.DataFrame(
        {
            "review_id": np.arange(1, n_rows + 1),
            "product_id": rng.integers(1, 500, size=n_rows),
            "user_id": rng.integers(1, 4_000, size=n_rows),
            "text": texts,
            "true_sentiment": labels,
        }
    )
    # Missing text in some rows
    m = rng.choice(df.index, size=int(n_rows * 0.015), replace=False)
    df.loc[m, "text"] = np.nan
    # Noisy text
    n_idx = rng.choice(df.index, size=int(n_rows * 0.02), replace=False)
    df.loc[n_idx, "text"] = df.loc[n_idx, "text"].astype(str) + " ###CORRUPT###"
    return df


def generate_basket_orders(n_orders: int = 25_000, seed: int = 44) -> pd.DataFrame:
    """One row per line item (order_id, product_id) for market basket mining."""
    rng = np.random.default_rng(seed)
    products = [f"P{i:03d}" for i in range(1, 81)]
    rows = []
    for oid in range(1, n_orders + 1):
        k = int(rng.integers(1, 6))  # 1-5 items per basket
        # Correlated baskets: often buy milk+bread, phone+case
        if rng.random() < 0.25:
            base = rng.choice(["P001", "P002", "P010", "P011", "P020", "P021"])
            basket = [base]
            if base in ("P001", "P002"):
                basket.append("P010" if "P001" in basket else "P011")
            while len(basket) < k:
                basket.append(rng.choice(products))
        else:
            basket = list(rng.choice(products, size=k, replace=False))
        for p in basket:
            rows.append({"order_id": oid, "product_id": p})
    df = pd.DataFrame(rows)
    # Missing product noise
    m = rng.choice(df.index, size=max(1, len(df) // 200), replace=False)
    df.loc[m, "product_id"] = np.nan
    return df


def generate_churn_users(n_rows: int = 15_000, seed: int = 45) -> pd.DataFrame:
    rng = np.random.default_rng(seed)
    tenure_months = rng.integers(0, 60, size=n_rows)
    monthly_spend = rng.lognormal(4.0, 0.8, size=n_rows)
    sessions_per_month = rng.poisson(8, size=n_rows).clip(0, 100)
    support_tickets = rng.poisson(1, size=n_rows)
    # Churn more likely with low tenure, low sessions, high tickets
    logit = (
        -2.0
        - 0.04 * tenure_months
        - 0.05 * sessions_per_month
        + 0.3 * support_tickets
        - 0.0002 * monthly_spend
    )
    p = 1 / (1 + np.exp(-logit))
    churned = (rng.random(n_rows) < p).astype(int)
    df = pd.DataFrame(
        {
            "user_id": np.arange(1, n_rows + 1),
            "tenure_months": tenure_months,
            "monthly_spend": np.round(monthly_spend, 2),
            "sessions_per_month": sessions_per_month,
            "support_tickets": support_tickets,
            "churned": churned,
        }
    )
    m = rng.choice(df.index, size=int(n_rows * 0.03), replace=False)
    df.loc[m, "monthly_spend"] = np.nan
    return df


def generate_ratings_purchases(n_interactions: int = 40_000, seed: int = 46) -> pd.DataFrame:
    """Implicit feedback: user_id, product_id, rating 1-5 for collaborative filtering."""
    rng = np.random.default_rng(seed)
    n_users = 3_000
    n_products = 200
    user_id = rng.integers(1, n_users + 1, size=n_interactions)
    product_id = rng.integers(1, n_products + 1, size=n_interactions)
    # Preference clusters
    pref = (user_id % 20) + (product_id % 20)
    rating = rng.normal(3.0 + 0.08 * (pref % 5), 1.0, size=n_interactions)
    rating = np.clip(np.round(rating), 1, 5).astype(int)
    df = pd.DataFrame({"user_id": user_id, "product_id": product_id, "rating": rating})
    m = rng.choice(df.index, size=int(n_interactions * 0.02), replace=False)
    df.loc[m, "rating"] = np.nan
    return df


def write_data_lake() -> dict[str, str]:
    """
    Persist datasets to the local data lake folder.
    Treat this directory as a stand-in for HDFS paths like /lake/ecomm/transactions/.
    """
    lake = _ensure_lake()
    paths = {}

    tx = generate_transactions()
    tx_path = lake / "transactions.csv"
    tx.to_csv(tx_path, index=False)
    paths["transactions_csv"] = str(tx_path)

    rev = generate_reviews()
    rev_path = lake / "reviews.json"
    rev.to_json(rev_path, orient="records", lines=True)
    paths["reviews_jsonl"] = str(rev_path)

    basket = generate_basket_orders()
    basket.to_csv(lake / "order_line_items.csv", index=False)
    paths["baskets_csv"] = str(lake / "order_line_items.csv")

    churn = generate_churn_users()
    churn.to_csv(lake / "user_churn_features.csv", index=False)
    paths["churn_csv"] = str(lake / "user_churn_features.csv")

    ratings = generate_ratings_purchases()
    ratings.to_csv(lake / "user_product_ratings.csv", index=False)
    paths["ratings_csv"] = str(lake / "user_product_ratings.csv")

    meta = {"description": "Simulated HDFS data lake layout", "files": paths}
    with open(lake / "lake_manifest.json", "w", encoding="utf-8") as f:
        json.dump(meta, f, indent=2)
    paths["manifest"] = str(lake / "lake_manifest.json")
    return paths


if __name__ == "__main__":
    write_data_lake()
    print("Data lake written to", DATA_LAKE)
