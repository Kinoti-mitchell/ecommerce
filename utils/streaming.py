"""
Simulated real-time streams (Kafka/Kinesis analog).

In production, events flow into a stream processor (Spark Streaming, Flink)
that applies the same models as batch with low latency. Here we use generators
over shuffled transaction slices and yield "live" recommendations from a
precomputed similarity matrix slice.
"""

from __future__ import annotations

from typing import Any, Callable, Iterator

import numpy as np
import pandas as pd


def streaming_transaction_batches(
    df: pd.DataFrame, batch_size: int = 500
) -> Iterator[pd.DataFrame]:
    """Simulate micro-batches (similar in spirit to Spark Structured Streaming windows)."""
    for i in range(0, len(df), batch_size):
        yield df.iloc[i : i + batch_size].copy()


def transaction_event_stream(
    df: pd.DataFrame, seed: int = 99
) -> Iterator[dict[str, Any]]:
    """Infinite-style iterator over randomized single-transaction dicts."""
    rng = np.random.default_rng(seed)
    idx = np.arange(len(df))
    while True:
        rng.shuffle(idx)
        for i in idx:
            row = df.iloc[int(i)]
            yield {
                "user_id": int(row["user_id"]),
                "amount": float(row["amount"]),
                "location_id": row["location_id"],
                "device_id": int(row["device_id"]),
                "timestamp": str(row["timestamp"]),
            }


def score_streaming_fraud(
    event: dict[str, Any],
    fraud_predict_fn: Callable[[pd.DataFrame], np.ndarray],
    user_home_location: dict[int, float],
    user_seen_devices: dict[int, set[int]],
) -> float:
    """
    Apply the trained fraud model to a single event with online feature flags.
    fraud_predict_fn expects a one-row DataFrame with engineered columns.
    """
    uid = event["user_id"]
    home = user_home_location.get(uid, event.get("location_id"))
    unusual_loc = 0
    if home is not None and not pd.isna(event.get("location_id")):
        unusual_loc = int(event["location_id"] != home)
    elif pd.isna(event.get("location_id")):
        unusual_loc = 1

    dev = event["device_id"]
    seen = user_seen_devices.setdefault(uid, set())
    new_device = int(dev not in seen)
    seen.add(dev)

    high_spend = int(event["amount"] > 500)
    row = pd.DataFrame(
        [
            {
                "user_id": uid,
                "amount": event["amount"],
                "location_id": event["location_id"] if not pd.isna(event.get("location_id")) else home,
                "device_id": dev,
                "unusual_location": unusual_loc,
                "high_spend": high_spend,
                "new_device": new_device,
            }
        ]
    )
    proba = fraud_predict_fn(row)
    return float(proba[0])


def recommend_for_user_live(
    user_id: int,
    user_item_matrix: np.ndarray,
    product_ids: list[int],
    user_ids: list[int],
    top_k: int = 5,
) -> list[tuple[int, float]]:
    """Dot-product style score using user row vs items (simplified CF online path)."""
    if user_id not in user_ids:
        return []
    u = user_ids.index(user_id)
    scores = user_item_matrix[u]
    top_idx = np.argsort(-scores)[:top_k]
    return [(product_ids[j], float(scores[j])) for j in top_idx if scores[j] > 0]
