"""
Central project configuration: paths, dataset sizes, and runtime modes.

Set environment variable STREAMLIT_QUICK=1 (or QUICK_MODE=1) for smaller synthetic
datasets and lighter training — better for Streamlit Community Cloud cold starts.
"""

from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path

# --- Repository layout (single source of truth for paths) ---
ROOT: Path = Path(__file__).resolve().parent
DATA_DIR: Path = ROOT / "data"
OUTPUT_DIR: Path = ROOT / "output"
MODELS_DIR: Path = ROOT / "models"


def quick_mode() -> bool:
    """Smaller data + faster steps when hosted or iterating."""
    return os.environ.get("STREAMLIT_QUICK", os.environ.get("QUICK_MODE", "")).lower() in (
        "1",
        "true",
        "yes",
    )


@dataclass(frozen=True)
class DataLakeSpec:
    """Row counts for each synthetic dataset."""

    n_transactions: int
    n_reviews: int
    n_basket_orders: int
    n_churn_users: int
    n_rating_interactions: int


def data_lake_spec() -> DataLakeSpec:
    if quick_mode():
        return DataLakeSpec(
            n_transactions=12_000,
            n_reviews=3_000,
            n_basket_orders=6_000,
            n_churn_users=4_000,
            n_rating_interactions=10_000,
        )
    return DataLakeSpec(
        n_transactions=55_000,
        n_reviews=12_000,
        n_basket_orders=25_000,
        n_churn_users=15_000,
        n_rating_interactions=40_000,
    )


def mapreduce_chunks() -> int:
    return 8 if quick_mode() else 16


def fraud_stream_batch_size() -> int:
    return 400 if quick_mode() else 800


def live_fraud_demo_events() -> int:
    return 30 if quick_mode() else 50
