"""
End-to-end batch pipeline: data lake → clean → models → output artifacts.

Kept separate from `main.py` so the entrypoint stays thin and Streamlit / tests
can call `run_full_pipeline()` directly.
"""

from __future__ import annotations

import json
import warnings
from datetime import datetime, timezone

import numpy as np
import pandas as pd

import config
from analytics.basket import mine_association_rules
from analytics.churn import churn_proba, train_churn_model
from analytics.fraud import engineer_fraud_features, fraud_proba, train_fraud_model
from analytics.recommendations import build_user_item_matrix, fit_user_cf, recommend_for_user
from analytics.sentiment import analyze_reviews
from project_summary import FINAL_SUMMARY_TEXT
from spark_jobs.batch_processing import write_spark_summary_output
from utils.cleaning import clean_baskets, clean_churn, clean_ratings, clean_reviews, clean_transactions
from utils.generate_datasets import write_data_lake
from utils.mapreduce_helpers import run_fraud_mapreduce

warnings.filterwarnings("ignore", category=FutureWarning)
warnings.filterwarnings("ignore", category=UserWarning, module="sklearn.utils.parallel")


def _ensure_outputs() -> None:
    config.OUTPUT_DIR.mkdir(parents=True, exist_ok=True)


def run_full_pipeline() -> None:
    _ensure_outputs()
    q = config.quick_mode()
    print("Step 1: Writing synthetic data lake (HDFS simulation)...")
    if q:
        print("  (QUICK_MODE / STREAMLIT_QUICK: smaller datasets)")
    write_data_lake()

    tx_path = config.DATA_DIR / "transactions.csv"
    raw_tx = pd.read_csv(tx_path)
    dirty_tx = raw_tx.copy()

    print("Step 2: Fraud model — dirty vs cleaned data (preprocessing lift)...")
    fraud_dirty = train_fraud_model(
        dirty_tx, model_suffix="fraud_rf_dirty", use_engineering=False
    )
    fraud_clean = train_fraud_model(clean_transactions(raw_tx), model_suffix="fraud_rf")

    tx_clean = clean_transactions(raw_tx)
    tx_feat = engineer_fraud_features(tx_clean)
    tx_feat["fraud_proba"] = fraud_proba(tx_clean)
    tx_feat.to_csv(config.OUTPUT_DIR / "fraud_scored_transactions.csv", index=False)

    print("Step 2b: Unsupervised transaction anomalies (Isolation Forest, no fraud labels)...")
    from analytics.anomalies import fit_transaction_anomalies, save_anomaly_outputs

    anom_res = fit_transaction_anomalies(tx_clean)
    save_anomaly_outputs(anom_res)

    print("Step 3: MapReduce-style fraud rollups (Python simulation)...")
    rollup = run_fraud_mapreduce(tx_clean, n_chunks=config.mapreduce_chunks())
    rollup.to_csv(config.OUTPUT_DIR / "fraud_user_rollups_mapreduce.csv", index=False)

    print("Step 4: Sentiment analysis...")
    rev = pd.read_json(config.DATA_DIR / "reviews.json", lines=True)
    rev_clean = clean_reviews(rev)
    rev_scored, sent_metrics = analyze_reviews(rev_clean)
    rev_scored.to_csv(config.OUTPUT_DIR / "sentiment_reviews.csv", index=False)

    print("Step 5: Market basket (Apriori)...")
    baskets = pd.read_csv(config.DATA_DIR / "order_line_items.csv")
    baskets_clean = clean_baskets(baskets)
    rules = pd.DataFrame()
    freq = pd.DataFrame()
    min_sup = 0.012 if q else 0.006
    freq, rules = mine_association_rules(
        baskets_clean, min_support=min_sup, min_threshold=0.25
    )
    if not rules.empty:
        rules.to_csv(config.OUTPUT_DIR / "association_rules.csv", index=False)
    if not freq.empty:
        freq.to_csv(config.OUTPUT_DIR / "frequent_itemsets.csv", index=False)

    print("Step 6: Churn model...")
    churn_df = pd.read_csv(config.DATA_DIR / "user_churn_features.csv")
    churn_clean = clean_churn(churn_df)
    churn_result = train_churn_model(churn_clean)
    churn_clean = churn_clean.copy()
    churn_clean["churn_proba"] = churn_proba(churn_clean)
    churn_clean.to_csv(config.OUTPUT_DIR / "churn_scores.csv", index=False)

    print("Step 7: Collaborative filtering...")
    ratings = pd.read_csv(config.DATA_DIR / "user_product_ratings.csv")
    ratings_clean = clean_ratings(ratings)
    fit_user_cf(ratings_clean)

    sample_users = ratings_clean["user_id"].drop_duplicates().head(15).tolist()
    rec_rows = []
    for u in sample_users:
        for pid, score in recommend_for_user(int(u), top_k=5):
            rec_rows.append({"user_id": u, "product_id": pid, "score": score})
    pd.DataFrame(rec_rows).to_csv(config.OUTPUT_DIR / "recommendations_sample.csv", index=False)

    print("Step 8: PySpark / pandas batch summary...")
    spark_out = write_spark_summary_output()

    print("Step 9: Simulated streaming (micro-batch fraud scores)...")
    from analytics.fraud import load_fraud_artifacts
    from utils.streaming import (
        recommend_for_user_live,
        score_streaming_fraud,
        streaming_transaction_batches,
        transaction_event_stream,
    )

    clf_stream, cols_stream = load_fraud_artifacts("fraud_rf")

    def _predict_batch(chunk: pd.DataFrame) -> np.ndarray:
        x = engineer_fraud_features(chunk)[cols_stream].fillna(0)
        return clf_stream.predict_proba(x)[:, 1]

    def _predict_engineered_row(row_df: pd.DataFrame) -> np.ndarray:
        return clf_stream.predict_proba(row_df[cols_stream].fillna(0))[:, 1]

    stream_rows = []
    bs = config.fraud_stream_batch_size()
    for batch in streaming_transaction_batches(tx_clean, batch_size=bs):
        probas = _predict_batch(batch)
        stream_rows.append(
            {
                "batch_start_idx": int(batch.index.min()),
                "batch_size": len(batch),
                "mean_fraud_proba": float(np.mean(probas)),
                "max_fraud_proba": float(np.max(probas)),
            }
        )
    pd.DataFrame(stream_rows).to_csv(config.OUTPUT_DIR / "streaming_fraud_batches.csv", index=False)

    gen = transaction_event_stream(tx_clean, seed=123)
    live_demo = []
    user_home = (
        tx_clean.groupby("user_id")["location_id"]
        .agg(lambda s: s.mode().iloc[0] if len(s.mode()) else s.median())
        .to_dict()
    )
    user_devices: dict[int, set[int]] = {}
    n_live = config.live_fraud_demo_events()
    for _ in range(n_live):
        ev = next(gen)
        p = score_streaming_fraud(ev, _predict_engineered_row, user_home, user_devices)
        live_demo.append({**{k: ev[k] for k in ("user_id", "amount")}, "fraud_proba": p})
    pd.DataFrame(live_demo).to_csv(config.OUTPUT_DIR / "streaming_fraud_live_sample.csv", index=False)

    centered, user_ids, product_ids = build_user_item_matrix(ratings_clean)
    uid_demo = int(user_ids[0])
    live_recs = recommend_for_user_live(uid_demo, centered, product_ids, user_ids, top_k=6)
    pd.DataFrame(live_recs, columns=["product_id", "score"]).assign(user_id=uid_demo).to_csv(
        config.OUTPUT_DIR / "streaming_recommendations_demo.csv", index=False
    )

    metrics = {
        "pipeline_mode": "quick" if q else "full",
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
        "transaction_anomalies": anom_res["summary"],
    }
    with open(config.OUTPUT_DIR / "metrics.json", "w", encoding="utf-8") as f:
        json.dump(metrics, f, indent=2, default=str)

    manifest = {
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "pipeline_mode": metrics["pipeline_mode"],
        "quick_mode": q,
    }
    with open(config.OUTPUT_DIR / "run_manifest.json", "w", encoding="utf-8") as mf:
        json.dump(manifest, mf, indent=2)
    hist_line = {
        "at": manifest["generated_at_utc"],
        "fraud_roc_auc_full": metrics["fraud_model_clean"]["roc_auc"],
        "fraud_roc_auc_baseline": metrics["fraud_model_dirty_baseline"]["roc_auc"],
        "churn_roc_auc": metrics["churn"]["roc_auc"],
    }
    with open(config.OUTPUT_DIR / "metrics_history.jsonl", "a", encoding="utf-8") as hf:
        hf.write(json.dumps(hist_line) + "\n")

    print("\n--- Key metrics (see output/metrics.json) ---")
    print("Fraud ROC-AUC (full pipeline):", metrics["fraud_model_clean"]["roc_auc"])
    print("Fraud ROC-AUC (amount-only baseline):", metrics["fraud_model_dirty_baseline"]["roc_auc"])
    print("Churn ROC-AUC:", metrics["churn"]["roc_auc"])
    print("Sentiment accuracy (vs synthetic labels):", metrics["sentiment"].get("accuracy_vs_synthetic_labels"))
    print("Association rules mined:", metrics["market_basket"]["n_rules"])
    print(
        "Anomaly outliers (Isolation Forest):",
        metrics["transaction_anomalies"]["n_flagged_outliers"],
        "/",
        metrics["transaction_anomalies"]["n_rows"],
    )
    print(FINAL_SUMMARY_TEXT)
