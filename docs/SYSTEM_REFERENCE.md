# E-commerce Big Data Analytics — System Reference

This document describes **every major part** of the repository: what it does, how it connects to the rest of the system, and where outputs live. It is aimed at developers, course reviewers, and anyone explaining the project end-to-end.

---

## 1. Purpose and high-level architecture

The project simulates a **batch analytics pipeline** over a **synthetic e-commerce data lake**, then exposes results in a **Streamlit** dashboard.

| Layer | Role |
|--------|------|
| **Data lake (`data/`)** | Stand-in for HDFS-style bulk files (CSV/JSON). Regenerated when the pipeline runs. |
| **Batch pipeline** | `pipeline/runner.py` → `run_full_pipeline()`: clean data, train models, score rows, run MapReduce-style and Spark/pandas aggregations, write `output/` and `models/`. |
| **CLI entry** | `main.py` calls `run_full_pipeline()`. |
| **Dashboard** | `streamlit_app.py` reads `output/metrics.json` and sample files; charts and tables; optional full retrain from the UI. |
| **`analytics/sandbox_score.py`** | Demo helper: score one hypothetical transaction using saved fraud + anomaly models. |
| **`notebooks/walkthrough.ipynb`** | Tiny clean → feature-engineering walkthrough. |
| **`tests/`** + **`.github/workflows/ci.yml`** | `pytest` smoke tests on push/PR. |

There is **no real production database**; all data is **synthetic** for teaching and demos.

---

## 2. Configuration (`config.py`)

| Piece | Purpose |
|--------|---------|
| **`ROOT`, `DATA_DIR`, `OUTPUT_DIR`, `MODELS_DIR`** | Central path definitions for the repo layout. |
| **`quick_mode()`** | Returns true if `STREAMLIT_QUICK` or `QUICK_MODE` env is set (1/true/yes). Smaller lakes and faster training for hosted apps. |
| **`DataLakeSpec` / `data_lake_spec()`** | Row counts for each synthetic dataset in quick vs full mode. |
| **`mapreduce_chunks()`** | Number of dataframe splits for the Python MapReduce simulation (8 quick / 16 full). |
| **`fraud_stream_batch_size()`** | Micro-batch size for simulated streaming fraud scoring. |
| **`live_fraud_demo_events()`** | Count of single-event fraud scores written to `streaming_fraud_live_sample.csv`. |

---

## 3. Environment variables (common)

| Variable | Effect |
|----------|--------|
| **`STREAMLIT_QUICK=1`** or **`QUICK_MODE=1`** | Smaller synthetic data and lighter pipeline (see `data_lake_spec()`). |
| **`USE_PYSPARK=1`** | `spark_jobs/batch_processing.py` uses real PySpark for transaction summary; otherwise **pandas chunked** read (same logical aggregation). |
| **`STREAMLIT_DISABLE_RETRAIN=1`** | Hides sidebar “retrain” button on public deployments. |
| **`STREAMLIT_RETRAIN_SECRET`** | If set, user must enter this password before the retrain button is enabled. |
| **`STREAMLIT_QUICK`** | Also read by Streamlit first-load messaging; same as quick mode for data. |

---

## 4. Data lake (`data/`)

Written by **`utils/generate_datasets.write_data_lake()`** (Step 1 of the pipeline). Sizes come from **`config.data_lake_spec()`**.

| File | Format | Contents |
|------|--------|----------|
| **`transactions.csv`** | CSV | `user_id`, `amount`, `location_id`, `device_id`, `timestamp`, `is_fraud`. Synthetic card-like payments; includes missing locations and bad amounts for cleaning demos. Fraud label is generated from latent rules (unusual location, high amount, new device). |
| **`reviews.json`** | JSON Lines | `review_id`, `product_id`, `user_id`, `text`, `true_sentiment`. Template phrases for positive/negative/neutral; some missing/corrupt text. Used for sentiment + accuracy vs `true_sentiment`. |
| **`order_line_items.csv`** | CSV | `order_id`, `product_id` — one row per line item. Correlated “baskets” (e.g. pairs of products) for association rules. Some missing `product_id`. |
| **`user_churn_features.csv`** | CSV | `user_id`, `tenure_months`, `monthly_spend`, `sessions_per_month`, `support_tickets`, `churned`. Logistic-style synthetic churn. |
| **`user_product_ratings.csv`** | CSV | `user_id`, `product_id`, `rating` (1–5). For user-based collaborative filtering. |
| **`lake_manifest.json`** | JSON | Lists generated paths (metadata for the “lake layout”). |
| **`spark_batch_summary.json`** | JSON | Written by **`write_spark_summary_output()`**: top users by spend (either PySpark or pandas-chunked engine). Lives under `data/` next to the lake. |

---

## 5. Batch pipeline (`pipeline/runner.py`)

**`run_full_pipeline()`** executes the following (console prints match these steps):

| Step | What runs | Main outputs |
|------|-----------|----------------|
| **1** | `write_data_lake()` | All files in `data/` above. |
| **2** | Fraud: `train_fraud_model` on **dirty** tx (amount-only RF) → `fraud_rf_dirty`; **cleaned** tx (full features) → `fraud_rf` | `models/fraud_rf*.joblib`, metrics inside return dicts. |
| **2 (cont.)** | `engineer_fraud_features` + `fraud_proba` on cleaned tx | `output/fraud_scored_transactions.csv` |
| **2b** | `fit_transaction_anomalies` + `save_anomaly_outputs` | `models/transaction_anomaly_if*.joblib`, `output/transaction_anomaly_scores.csv`, `output/transaction_anomalies_top500.csv` |
| **3** | `run_fraud_mapreduce` | `output/fraud_user_rollups_mapreduce.csv` |
| **4** | `clean_reviews` + `analyze_reviews` | `output/sentiment_reviews.csv`; sentiment metrics for `metrics.json` |
| **5** | `mine_association_rules` (Apriori or fallback) | `output/association_rules.csv`, `output/frequent_itemsets.csv` |
| **6** | `train_churn_model` + `churn_proba` | `models/churn_gb.joblib`, `output/churn_scores.csv` |
| **7** | `fit_user_cf` + sample `recommend_for_user` | `models/cf_user_item.npz`, `models/cf_meta.joblib`, `output/recommendations_sample.csv` |
| **8** | `write_spark_summary_output` | `data/spark_batch_summary.json` |
| **9** | Simulated streaming: batch fraud stats, live event fraud scores, live CF demo | `output/streaming_fraud_batches.csv`, `streaming_fraud_live_sample.csv`, `streaming_recommendations_demo.csv` |

Finally **`output/metrics.json`** is written with fraud (clean + baseline), sentiment, churn, basket counts, CF matrix sizes, data lake stats, MapReduce user count, anomaly summary, and notes. The runner also writes **`output/run_manifest.json`** (run metadata) and appends one line to **`output/metrics_history.jsonl`** (ROC snapshot per run).

---

## 6. Analytics package (`analytics/`)

| Module | Responsibility |
|--------|----------------|
| **`fraud.py`** | **`engineer_fraud_features`**: `unusual_location`, `high_spend` (vs user p95), `new_device` (time-ordered). **`train_fraud_model`**: RandomForest (80 trees, balanced class weight); full model uses `amount` + engineered columns; baseline uses **amount only** on dirty data. **`fraud_proba`**, **`load_fraud_artifacts`**. |
| **`anomalies.py`** | **Unsupervised** Isolation Forest on the same four numeric features **without** using `is_fraud` for training. **`anomaly_score`** = negative `score_samples` (higher = rarer). Saves IF model + top-500 CSV for the UI. |
| **`sentiment.py`** | TextBlob polarity → `blob_label` → `positive` / `negative` / `neutral`. Metrics vs `true_sentiment` when present. |
| **`churn.py`** | GradientBoostingClassifier on tenure, monthly_spend, sessions_per_month, support_tickets; predicts `churned`. |
| **`basket.py`** | Groups orders into baskets; **mlxtend Apriori + association_rules** when available, else **pandas pairwise fallback** for frequent pairs and rules. |
| **`recommendations.py`** | Pivot to user×product matrix, mean-center per user, **cosine similarity** between users, neighbor-weighted scores for **`recommend_for_user`**. Artifacts in `.npz` + `cf_meta.joblib`. |
| **`sandbox_score.py`** | **`score_hypothetical_transaction`**: append one row for a user, run clean + feature engineering, apply saved fraud RF + IF (for Streamlit “hypothetical transaction” demo). |

---

## 7. Utilities (`utils/`)

| Module | Responsibility |
|--------|----------------|
| **`generate_datasets.py`** | All **`generate_*`** functions and **`write_data_lake`**. Creates synthetic transactions, reviews, baskets, churn users, ratings; introduces missing/invalid values for ETL demos. |
| **`cleaning.py`** | **`clean_transactions`**: user-mode imputation for `location_id`, fix bad `amount`. **`clean_reviews`**, **`clean_baskets`**, **`clean_churn`**, **`clean_ratings`**. |
| **`mapreduce_helpers.py`** | Generic **`chunk_dataframe`**, **`map_phase`**, **`shuffle_sort`**, **`reduce_phase`**. Fraud-specific **`fraud_map_chunk`** / **`fraud_reduce_user`** / **`run_fraud_mapreduce`**. |
| **`streaming.py`** | **`streaming_transaction_batches`**, **`transaction_event_stream`**, **`score_streaming_fraud`** (online-style features + call to fraud model), **`recommend_for_user_live`** for demo recs. |

---

## 8. Spark jobs (`spark_jobs/batch_processing.py`)

| Function | Purpose |
|----------|---------|
| **`run_spark_transaction_summary`** | If PySpark imports work: SparkSession `local[*]`, read transactions CSV, **groupBy user_id** → count, sum, max amount, top 20 by spend. Returns `{"engine": "pyspark", ...}`. |
| **`pandas_chunked_summary`** | Same **logical** aggregation using **pandas `read_csv(chunksize=...)`** + combine (reduce across chunks). |
| **`write_spark_summary_output`** | Chooses Spark if `USE_PYSPARK=1` and Spark succeeds; else pandas path. Writes **`data/spark_batch_summary.json`**. |

---

## 9. Models directory (`models/`)

Artifacts created by the pipeline (not all need to be committed for CI; often regenerated):

| Artifact | Producer |
|----------|----------|
| **`fraud_rf.joblib`**, **`fraud_rf_feature_cols.joblib`** | Supervised fraud (clean pipeline). |
| **`fraud_rf_dirty.joblib`**, **`fraud_rf_dirty_feature_cols.joblib`** | Amount-only baseline. |
| **`transaction_anomaly_if.joblib`**, **`transaction_anomaly_if_cols.joblib`** | Isolation Forest anomalies. |
| **`churn_gb.joblib`**, **`churn_feature_cols.joblib`** | Churn model. |
| **`cf_user_item.npz`** | Centered user–item matrix + similarity (saved compressed). |
| **`cf_meta.joblib`** | `user_ids`, `product_ids`, `top_similar`. |

---

## 10. Output directory (`output/`)

| File | Description |
|------|-------------|
| **`metrics.json`** | Single source of truth for dashboard KPIs and the **Report** tab. |
| **`fraud_scored_transactions.csv`** | Transactions + engineered features + `fraud_proba`. |
| **`transaction_anomaly_scores.csv`** | All rows with anomaly score and IF outlier flag. |
| **`transaction_anomalies_top500.csv`** | Top 500 by anomaly score (Streamlit table/plot). |
| **`fraud_user_rollups_mapreduce.csv`** | Per-user aggregates from MapReduce simulation. |
| **`sentiment_reviews.csv`** | Reviews + polarity + predicted sentiment. |
| **`association_rules.csv`**, **`frequent_itemsets.csv`** | Basket mining results. |
| **`churn_scores.csv`** | Users + `churn_proba`. |
| **`recommendations_sample.csv`** | Sample user recommendations. |
| **`streaming_fraud_batches.csv`** | Per-batch mean/max fraud probability. |
| **`streaming_fraud_live_sample.csv`** | Event-level streaming fraud demo. |
| **`streaming_recommendations_demo.csv`** | Small live CF demo. |
| **`run_manifest.json`** | UTC timestamp, pipeline mode, quick flag (last run). |
| **`metrics_history.jsonl`** | One JSON line per pipeline run (append-only ROC-AUC snapshot). |

---

## 11. Dashboard package (`ecom_dashboard/`)

| File | Role |
|------|------|
| **`loaders.py`** | Read `metrics.json`, sample transactions/reviews, rules, churn scores, sentiment CSV, **anomaly top-500**. |
| **`explanations.py`** | Markdown strings for expanders (overview, tabs, training, anomalies, report, **architecture ASCII**). |
| **`ui.py`** | **`inject_custom_css`**, **`polish_fig`** (Plotly layout), **`plotly_config`**, fraud/sentiment color constants. |
| **`findings_report.py`** | **`build_findings_report_markdown(metrics)`** for the Report tab and download. |
| **`__init__.py`** | Package marker. |

---

## 12. Streamlit application (`streamlit_app.py`)

| Area | Behavior |
|------|----------|
| **Startup** | If `output/metrics.json` is missing, runs **`main.main()`** once (cold start on Cloud), then reruns. |
| **Page config** | Wide layout, title, icon. |
| **CSS** | `ui_theme.inject_custom_css()`. |
| **Hero KPIs** | Fraud ROC-AUC (full + baseline), churn ROC-AUC, sentiment accuracy. |
| **Sidebar** | User ID, Top-K, fraud chart sample size; model snapshot metrics; **Training / pipeline** expander (optional full retrain; `STREAMLIT_DISABLE_RETRAIN` / `STREAMLIT_RETRAIN_SECRET`). |
| **Main (top)** | **How to navigate** info + **Architecture snapshot** expander. |
| **Fraud tab** | Histograms/deciles; **Try a hypothetical transaction**; model comparison; **Alert-style counts**; supervised scatter sample; **Isolation Forest** section. |
| **Sentiment tab** | Pie/histogram, accuracy metric. |
| **Recommendations tab** | Table + bar chart for selected user. |
| **Churn tab** | Table sample, histogram, ROC metric. |
| **Market basket tab** | Rules table, scatter confidence vs lift. |
| **Detections report tab** (second tab) | Auto-generated findings markdown + **download .md**; **metrics history** + **run manifest** expanders when files exist. |
| **Big Data summary tab** | Hadoop/Spark/business bullets + full **`project_summary.FINAL_SUMMARY_TEXT`**. |

---

## 13. Streamlit theme (`.streamlit/config.toml`)

Theme colors for **dark/light** tables (`[theme]`, `[theme.dark]`, `[theme.light]`, sidebars) so the app chrome matches custom CSS. Adjust **primary**, **background**, **text** for hosted branding.

---

## 14. Project text (`project_summary.py`)

**`FINAL_SUMMARY_TEXT`**: long printable summary (Big Data value, opportunities, challenges, Hadoop vs Spark, pointer to `data/`, MapReduce, PySpark, fraud + **anomalies**). Shown in Streamlit expander and printed at end of pipeline run.

---

## 15. Dependencies (`requirements.txt`)

Core stack: **pandas**, **numpy**, **scikit-learn**, **plotly**, **streamlit**, **textblob**, **nltk**, **mlxtend**, **joblib**, **pytest**; **pyspark** listed for optional Spark path (needs Java when enabled).

---

## 16. Other documentation

| File | Role |
|------|------|
| **`README.md`** | Quick start: install, `python main.py`, `streamlit run`, Cloud notes. |
| **`docs/PRESENTATION.md`** | Slide-oriented / narrative material for the project (if present). |
| **`docs/SYSTEM_REFERENCE.md`** | **This file** — full component reference. |
| **`docs/PARTITIONS.md`** | Concept note on partitioned lakes vs flat `data/` in this demo. |

---

## 17. End-to-end data flow (summary)

```text
config.py (paths, quick mode)
       ↓
write_data_lake() → data/*.csv|json
       ↓
run_full_pipeline()
  → cleaning → fraud (supervised + scores) → anomalies (unsupervised)
  → MapReduce rollups → sentiment → baskets → churn → CF
  → Spark/pandas summary → streaming demos
       ↓
models/* , output/* , data/spark_batch_summary.json
       ↓
streamlit_app.py reads metrics + samples → tabs + report
```

---

*Last updated to match the repository layout and pipeline as of this document’s authoring. If you add modules or steps, update this file alongside `pipeline/runner.py`.*
