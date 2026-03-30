"""
E-commerce Big Data analytics pipeline (batch).

Run once to:
1. Populate the data lake (simulated HDFS folder `data/`)
2. Train/evaluate models and write metrics + CSV outputs for Streamlit
3. Batch aggregation via pandas chunks (set USE_PYSPARK=1 for local PySpark)

Usage:
    python main.py
"""

from __future__ import annotations

import json
import warnings
from pathlib import Path

import numpy as np

warnings.filterwarnings("ignore", category=FutureWarning)
warnings.filterwarnings("ignore", category=UserWarning, module="sklearn.utils.parallel")
import pandas as pd

from analytics.basket import mine_association_rules
from analytics.churn import churn_proba, train_churn_model
from analytics.fraud import engineer_fraud_features, fraud_proba, train_fraud_model
from analytics.recommendations import fit_user_cf, recommend_for_user
from analytics.sentiment import analyze_reviews
from utils.cleaning import clean_baskets, clean_churn, clean_ratings, clean_reviews, clean_transactions
from utils.generate_datasets import write_data_lake
from utils.mapreduce_helpers import run_fraud_mapreduce
from spark_jobs.batch_processing import write_spark_summary_output

ROOT = Path(__file__).resolve().parent
OUTPUT = ROOT / "output"


FINAL_SUMMARY_TEXT = """
================================================================================
BIG DATA IN E-COMMERCE — SUMMARY (FOR LEARNERS)
================================================================================

How Big Data improves e-commerce
-------------------------------
• Personalization: Mining clicks, purchases, and reviews at scale lets retailers
  tailor recommendations and content (collaborative filtering, segment models).
• Fraud prevention: High-volume transaction streams feed models that flag
  anomalous spend, devices, and locations in near real time.
• Customer retention: Behavioral features (tenure, engagement, support load)
  power churn models so teams can intervene with offers or fixes.
• Revenue growth: Basket analysis surfaces cross-sell bundles; sentiment
  tracks product quality and NPS drivers across huge review corpora.

Opportunities
-------------
• Dynamic pricing: Demand, inventory, and competitor signals updated frequently.
• Targeted marketing: Audience building from unified lake + streaming events.
• Scalability: Horizontal storage (HDFS/object store) and compute (Spark/K8s)
  absorb peak traffic and seasonal loads.

Challenges
----------
• Data privacy: GDPR/CCPA, consent, and minimizing PII in analytical zones.
• System complexity: Many moving parts (ingest, catalog, jobs, serving).
• Infrastructure cost: Storage replication and always-on clusters need tuning
  (spot instances, autoscaling, lakehouse patterns).

Role of Hadoop-era components vs Spark
--------------------------------------
• HDFS: Cheap, fault-tolerant storage for massive files; today often complemented
  by object stores (S3, ADLS) with table formats (Iceberg, Delta).
• MapReduce: Batch map/shuffle/reduce paradigm for parallel aggregation; still
  the conceptual backbone of distributed "split-process-combine" workloads.
• Apache Spark: In-memory (where possible) DataFrame/RDD APIs, SQL, MLlib, and
  Structured Streaming — common successor to MapReduce for analytics and ML.

This project simulates HDFS with the `data/` lake, MapReduce-style Python
aggregations in `utils/mapreduce_helpers.py`, and optional PySpark in
`spark_jobs/batch_processing.py`.
================================================================================
"""


def ensure_outputs() -> None:
    OUTPUT.mkdir(parents=True, exist_ok=True)


def main() -> None:
    ensure_outputs()
    print("Step 1: Writing synthetic data lake (HDFS simulation)...")
    write_data_lake()

    tx_path = ROOT / "data" / "transactions.csv"
    raw_tx = pd.read_csv(tx_path)
    # Dirty baseline: train on raw amount only (no engineered risk signals, no imputation)
    dirty_tx = raw_tx.copy()

    print("Step 2: Fraud model — dirty vs cleaned data (preprocessing lift)...")
    fraud_dirty = train_fraud_model(
        dirty_tx, model_suffix="fraud_rf_dirty", use_engineering=False
    )
    fraud_clean = train_fraud_model(clean_transactions(raw_tx), model_suffix="fraud_rf")

    tx_clean = clean_transactions(raw_tx)
    tx_feat = engineer_fraud_features(tx_clean)
    tx_feat["fraud_proba"] = fraud_proba(tx_clean)
    tx_feat.to_csv(OUTPUT / "fraud_scored_transactions.csv", index=False)

    # MapReduce-style user rollups
    print("Step 3: MapReduce-style fraud rollups (Python simulation)...")
    rollup = run_fraud_mapreduce(tx_clean, n_chunks=16)
    rollup.to_csv(OUTPUT / "fraud_user_rollups_mapreduce.csv", index=False)

    print("Step 4: Sentiment analysis...")
    rev = pd.read_json(ROOT / "data" / "reviews.json", lines=True)
    rev_clean = clean_reviews(rev)
    rev_scored, sent_metrics = analyze_reviews(rev_clean)
    rev_scored.to_csv(OUTPUT / "sentiment_reviews.csv", index=False)

    print("Step 5: Market basket (Apriori)...")
    baskets = pd.read_csv(ROOT / "data" / "order_line_items.csv")
    baskets_clean = clean_baskets(baskets)
    rules = pd.DataFrame()
    freq = pd.DataFrame()
    freq, rules = mine_association_rules(baskets_clean, min_support=0.006, min_threshold=0.25)
    if not rules.empty:
        rules.to_csv(OUTPUT / "association_rules.csv", index=False)
    if not freq.empty:
        freq.to_csv(OUTPUT / "frequent_itemsets.csv", index=False)

    print("Step 6: Churn model...")
    churn_df = pd.read_csv(ROOT / "data" / "user_churn_features.csv")
    churn_clean = clean_churn(churn_df)
    churn_result = train_churn_model(churn_clean)
    churn_clean = churn_clean.copy()
    churn_clean["churn_proba"] = churn_proba(churn_clean)
    churn_clean.to_csv(OUTPUT / "churn_scores.csv", index=False)

    print("Step 7: Collaborative filtering...")
    ratings = pd.read_csv(ROOT / "data" / "user_product_ratings.csv")
    ratings_clean = clean_ratings(ratings)
    fit_user_cf(ratings_clean)

    # Sample recommendations for a few users
    sample_users = ratings_clean["user_id"].drop_duplicates().head(15).tolist()
    rec_rows = []
    for u in sample_users:
        for pid, score in recommend_for_user(int(u), top_k=5):
            rec_rows.append({"user_id": u, "product_id": pid, "score": score})
    pd.DataFrame(rec_rows).to_csv(OUTPUT / "recommendations_sample.csv", index=False)

    print("Step 8: PySpark / pandas batch summary...")
    spark_out = write_spark_summary_output()

    print("Step 9: Simulated streaming (micro-batch fraud scores)...")
    from analytics.fraud import load_fraud_artifacts
    from utils.streaming import streaming_transaction_batches, transaction_event_stream

    clf_stream, cols_stream = load_fraud_artifacts("fraud_rf")

    def _predict_batch(chunk: pd.DataFrame) -> np.ndarray:
        x = engineer_fraud_features(chunk)[cols_stream].fillna(0)
        return clf_stream.predict_proba(x)[:, 1]

    def _predict_engineered_row(row_df: pd.DataFrame) -> np.ndarray:
        """For hand-built rows that already match training feature columns."""
        return clf_stream.predict_proba(row_df[cols_stream].fillna(0))[:, 1]

    stream_rows = []
    for batch in streaming_transaction_batches(tx_clean, batch_size=800):
        probas = _predict_batch(batch)
        stream_rows.append(
            {
                "batch_start_idx": int(batch.index.min()),
                "batch_size": len(batch),
                "mean_fraud_proba": float(np.mean(probas)),
                "max_fraud_proba": float(np.max(probas)),
            }
        )
    pd.DataFrame(stream_rows).to_csv(OUTPUT / "streaming_fraud_batches.csv", index=False)

    # A few "live" single-event scores (generator demo)
    gen = transaction_event_stream(tx_clean, seed=123)
    live_demo = []
    user_home = (
        tx_clean.groupby("user_id")["location_id"]
        .agg(lambda s: s.mode().iloc[0] if len(s.mode()) else s.median())
        .to_dict()
    )
    user_devices: dict[int, set[int]] = {}
    from utils.streaming import score_streaming_fraud

    for _ in range(50):
        ev = next(gen)
        p = score_streaming_fraud(ev, _predict_engineered_row, user_home, user_devices)
        live_demo.append({**{k: ev[k] for k in ("user_id", "amount")}, "fraud_proba": p})
    pd.DataFrame(live_demo).to_csv(OUTPUT / "streaming_fraud_live_sample.csv", index=False)

    # Live-style CF: top picks for one user from factorized row
    from analytics.recommendations import build_user_item_matrix

    centered, user_ids, product_ids = build_user_item_matrix(ratings_clean)
    uid_demo = int(user_ids[0])
    from utils.streaming import recommend_for_user_live

    live_recs = recommend_for_user_live(uid_demo, centered, product_ids, user_ids, top_k=6)
    pd.DataFrame(live_recs, columns=["product_id", "score"]).assign(user_id=uid_demo).to_csv(
        OUTPUT / "streaming_recommendations_demo.csv", index=False
    )

    metrics = {
        "fraud_model_clean": fraud_clean["metrics"],
        "fraud_model_dirty_baseline": fraud_dirty["metrics"],
        "preprocessing_note": (
            "Dirty baseline = RandomForest on transaction amount only (no location/device features, "
            "no cleaning). Clean pipeline = group-aware imputation + engineered fraud features."
        ),
        "sentiment": sent_metrics,
        "churn": churn_result["metrics"],
        "market_basket": {
            "n_rules": int(len(rules)) if rules is not None else 0,
            "n_frequent_itemsets": int(len(freq)) if freq is not None else 0,
        },
        "collaborative_filtering": {
            "n_users_in_matrix": len(user_ids),
            "n_products_in_matrix": len(product_ids),
        },
        "data_lake": {
            "transactions_rows": len(raw_tx),
            "spark_summary_path": spark_out,
        },
        "mapreduce_rollup_users": len(rollup),
    }
    with open(OUTPUT / "metrics.json", "w", encoding="utf-8") as f:
        json.dump(metrics, f, indent=2, default=str)

    print("\n--- Key metrics (see output/metrics.json) ---")
    print("Fraud ROC-AUC (full pipeline):", metrics["fraud_model_clean"]["roc_auc"])
    print("Fraud ROC-AUC (amount-only baseline):", metrics["fraud_model_dirty_baseline"]["roc_auc"])
    print("Churn ROC-AUC:", metrics["churn"]["roc_auc"])
    print("Sentiment accuracy (vs synthetic labels):", metrics["sentiment"].get("accuracy_vs_synthetic_labels"))
    print("Association rules mined:", metrics["market_basket"]["n_rules"])
    print(FINAL_SUMMARY_TEXT)


if __name__ == "__main__":
    main()
