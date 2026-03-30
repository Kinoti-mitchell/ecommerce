"""
Collaborative filtering (user-based) using cosine similarity.

Spark ALS on HDFS is the industrial scale variant; this mirrors the idea
with dense user-item matrices for medium-sized catalogs.
"""

from __future__ import annotations

from pathlib import Path

import joblib
import numpy as np
import pandas as pd
from sklearn.metrics.pairwise import cosine_similarity

ROOT = Path(__file__).resolve().parent.parent
MODEL_DIR = ROOT / "models"


def build_user_item_matrix(df: pd.DataFrame) -> tuple[np.ndarray, list[int], list[int]]:
    """Mean-centered ratings matrix: rows users, columns products."""
    pivot = df.pivot_table(
        index="user_id", columns="product_id", values="rating", aggfunc="mean"
    )
    product_ids = [int(c) for c in pivot.columns]
    user_ids = [int(i) for i in pivot.index]
    mat = pivot.to_numpy()
    mat = np.nan_to_num(mat, nan=0.0)
    user_means = np.where(mat.sum(axis=1, keepdims=True) > 0, mat.sum(axis=1, keepdims=True) / (mat > 0).sum(axis=1, keepdims=True).clip(min=1), 0)
    centered = mat - user_means
    centered = np.where(mat > 0, centered, 0)
    return centered, user_ids, product_ids


def fit_user_cf(df: pd.DataFrame, top_similar: int = 40) -> dict:
    centered, user_ids, product_ids = build_user_item_matrix(df)
    sim = cosine_similarity(centered)
    np.fill_diagonal(sim, 0)
    MODEL_DIR.mkdir(parents=True, exist_ok=True)
    artifact = {
        "user_item_centered": centered,
        "similarity": sim,
        "user_ids": user_ids,
        "product_ids": product_ids,
        "top_similar": top_similar,
    }
    np.savez_compressed(MODEL_DIR / "cf_user_item.npz", centered=centered, sim=sim)
    joblib.dump(
        {"user_ids": user_ids, "product_ids": product_ids, "top_similar": top_similar},
        MODEL_DIR / "cf_meta.joblib",
    )
    return artifact


def recommend_for_user(
    user_id: int,
    artifact: dict | None = None,
    top_k: int = 8,
) -> list[tuple[int, float]]:
    if artifact is None:
        z = np.load(MODEL_DIR / "cf_user_item.npz")
        centered = z["centered"]
        sim = z["sim"]
        meta = joblib.load(MODEL_DIR / "cf_meta.joblib")
        user_ids = meta["user_ids"]
        product_ids = meta["product_ids"]
        top_similar = meta["top_similar"]
    else:
        centered = artifact["user_item_centered"]
        sim = artifact["similarity"]
        user_ids = artifact["user_ids"]
        product_ids = artifact["product_ids"]
        top_similar = artifact["top_similar"]

    if user_id not in user_ids:
        return []
    ui = user_ids.index(user_id)
    neigh = np.argsort(-sim[ui])[:top_similar]
    scores = np.zeros(centered.shape[1])
    for v in neigh:
        w = sim[ui, v]
        if w <= 0:
            continue
        scores += w * centered[v]
    # Mask already rated
    rated = centered[ui] != 0
    scores[rated] = -1e9
    top_idx = np.argsort(-scores)[:top_k]
    return [(product_ids[j], float(scores[j])) for j in top_idx if scores[j] > -1e8]
