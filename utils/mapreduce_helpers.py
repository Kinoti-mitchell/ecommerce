"""
Simulated MapReduce-style processing (conceptual Hadoop).

How Hadoop MapReduce would work at scale:
- **Map**: Each mapper reads an HDFS input split (a chunk of a large file).
  It emits key-value pairs, e.g. (user_id, amount) or (word, 1).
- **Shuffle/Sort**: Framework groups all values by key across the cluster.
- **Reduce**: Reducers aggregate values per key (sums, counts, top-N).

In real e-commerce:
- Batch fraud rollups (daily spend per card), log parsing, ETL to the data warehouse.

This module implements the same pattern in pure Python over DataFrame chunks
so beginners can see map→reduce without a cluster. PySpark RDD/DataFrame APIs
are the modern replacement for classic MapReduce on the same HDFS data.
"""

from __future__ import annotations

from collections import defaultdict
from typing import Callable, Iterable, Iterator, TypeVar

import numpy as np
import pandas as pd

K = TypeVar("K")
V = TypeVar("V")
R = TypeVar("R")


def chunk_dataframe(df: pd.DataFrame, n_chunks: int) -> list[pd.DataFrame]:
    return np.array_split(df, n_chunks)


def map_phase(
    chunks: list[pd.DataFrame],
    mapper: Callable[[pd.DataFrame], list[tuple[K, V]]],
) -> list[tuple[K, V]]:
    """Apply mapper to each chunk (parallel mappers in Hadoop)."""
    out: list[tuple[K, V]] = []
    for ch in chunks:
        out.extend(mapper(ch))
    return out


def shuffle_sort(pairs: list[tuple[K, V]]) -> dict[K, list[V]]:
    """Group values by key (framework shuffle in Hadoop)."""
    d: dict[K, list[V]] = defaultdict(list)
    for k, v in pairs:
        d[k].append(v)
    return dict(d)


def reduce_phase(
    grouped: dict[K, list[V]],
    reducer: Callable[[K, Iterable[V]], R],
) -> dict[K, R]:
    """One reducer invocation per key (possibly many reducer tasks in Hadoop)."""
    return {k: reducer(k, vals) for k, vals in grouped.items()}


# --- Concrete mappers/reducers for fraud analytics ---


def fraud_map_chunk(chunk: pd.DataFrame) -> list[tuple[int, dict]]:
    """
    Emit (user_id, partial_stats) per user **within this split** (combiner-style).

    In Hadoop you can use a combiner to pre-aggregate map output per key inside
    the map task; here we do the same to keep the demo fast on one machine.
    """
    c = chunk.copy()
    c["unusual_loc"] = c["location_id"].isna().astype(int)
    c["high_amt"] = (c["amount"].astype(float) > 500).astype(int)
    g = c.groupby("user_id", sort=False).agg(
        count=("user_id", "size"),
        sum_amount=("amount", "sum"),
        unusual_loc=("unusual_loc", "sum"),
        high_amt=("high_amt", "sum"),
    )
    pairs: list[tuple[int, dict]] = []
    for uid, row in g.iterrows():
        pairs.append(
            (
                int(uid),
                {
                    "count": int(row["count"]),
                    "sum_amount": float(row["sum_amount"]),
                    "unusual_loc": int(row["unusual_loc"]),
                    "high_amt": int(row["high_amt"]),
                },
            )
        )
    return pairs


def fraud_reduce_user(_uid: int, partials: Iterable[dict]) -> dict:
    """Aggregate all transactions for one user."""
    total_c = 0
    total_sum = 0.0
    u_loc = 0
    high = 0
    for p in partials:
        total_c += p["count"]
        total_sum += p["sum_amount"]
        u_loc += p["unusual_loc"]
        high += p["high_amt"]
    return {
        "txn_count": total_c,
        "total_amount": round(total_sum, 2),
        "rows_missing_location": u_loc,
        "high_amount_txns": high,
    }


def run_fraud_mapreduce(df: pd.DataFrame, n_chunks: int = 8) -> pd.DataFrame:
    chunks = chunk_dataframe(df, n_chunks)
    mapped = map_phase(chunks, fraud_map_chunk)
    grouped = shuffle_sort(mapped)
    reduced = reduce_phase(grouped, fraud_reduce_user)
    rows = [{"user_id": k, **v} for k, v in reduced.items()]
    return pd.DataFrame(rows).sort_values("user_id").reset_index(drop=True)


