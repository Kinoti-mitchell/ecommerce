"""
Streamlit dashboard for the e-commerce Big Data analytics demo.

Run:
    streamlit run streamlit_app.py

Ensure `python main.py` has been executed once to generate `output/` and `data/`.
"""

from __future__ import annotations

import sys
from pathlib import Path

import pandas as pd
import plotly.express as px
import streamlit as st

ROOT = Path(__file__).resolve().parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from analytics.fraud import engineer_fraud_features, load_fraud_artifacts
from analytics.recommendations import recommend_for_user
from dashboard.loaders import (
    load_churn_scores,
    load_metrics,
    load_reviews_sample,
    load_rules,
    load_sentiment_results,
    load_transactions_sample,
)
from main import FINAL_SUMMARY_TEXT

st.set_page_config(
    page_title="E‑commerce Big Data Analytics",
    layout="wide",
    initial_sidebar_state="expanded",
)

st.title("E‑commerce Big Data Analytics Lab")
st.caption(
    "Simulated data lake (HDFS-style `data/`), MapReduce-style rollups, optional PySpark, and Streamlit."
)

metrics = load_metrics()
if not metrics:
    st.warning("No `output/metrics.json` found. Run `python main.py` from the project root first.")
    st.stop()

# --- Sidebar ---
st.sidebar.header("Interactive inputs")
user_pick = st.sidebar.number_input("User ID for recommendations", min_value=1, value=1, step=1)
top_k = st.sidebar.slider("Top‑K recommendations", 3, 15, 6)
fraud_sample_n = st.sidebar.slider("Fraud chart sample (rows)", 1000, 15000, 6000)

st.sidebar.markdown("---")
st.sidebar.subheader("Metrics snapshot")
st.sidebar.metric("Fraud ROC‑AUC (full pipeline)", f"{metrics['fraud_model_clean']['roc_auc']:.3f}")
st.sidebar.metric("Fraud ROC‑AUC (amount‑only baseline)", f"{metrics['fraud_model_dirty_baseline']['roc_auc']:.3f}")
st.sidebar.metric("Churn ROC‑AUC", f"{metrics['churn']['roc_auc']:.3f}")

# --- Tabs ---
tab_fraud, tab_sent, tab_rec, tab_churn, tab_basket, tab_summary = st.tabs(
    ["Fraud", "Sentiment", "Recommendations", "Churn", "Market basket", "Big Data summary"]
)

with tab_fraud:
    st.subheader("Fraud detection dashboard")
    tx = load_transactions_sample(fraud_sample_n)
    if tx.empty:
        st.info("No transaction data.")
    else:
        c1, c2 = st.columns(2)
        with c1:
            st.markdown("**Amount distribution (sample)**")
            fig_hist = px.histogram(tx, x="amount", nbins=60, color="is_fraud", barmode="overlay")
            st.plotly_chart(fig_hist, use_container_width=True)
        with c2:
            st.markdown("**Fraud rate by amount decile**")
            tx2 = tx.copy()
            tx2["decile"] = pd.qcut(tx2["amount"], q=10, labels=False, duplicates="drop")
            rate = tx2.groupby("decile")["is_fraud"].mean().reset_index()
            fig_bar = px.bar(rate, x="decile", y="is_fraud", labels={"is_fraud": "fraud rate"})
            st.plotly_chart(fig_bar, use_container_width=True)

        st.markdown("**Feature + cleaning impact (amount‑only vs full pipeline)**")
        fc = metrics["fraud_model_clean"]
        fd = metrics["fraud_model_dirty_baseline"]
        comp = pd.DataFrame(
            {
                "pipeline": ["Full: clean + engineered features", "Baseline: amount only"],
                "ROC‑AUC": [fc["roc_auc"], fd["roc_auc"]],
                "Accuracy": [fc["accuracy"], fd["accuracy"]],
            }
        )
        st.dataframe(comp, use_container_width=True)
        fig_cmp = px.bar(comp, x="pipeline", y="ROC‑AUC", color="pipeline")
        st.plotly_chart(fig_cmp, use_container_width=True)

        st.markdown("**Live fraud probability (reload model, score sample)**")
        try:
            clf, cols = load_fraud_artifacts("fraud_rf")
            small = tx.head(200).copy()
            xf = engineer_fraud_features(small)
            p = clf.predict_proba(xf[cols].fillna(0))[:, 1]
            small = small.reset_index(drop=True)
            small["fraud_proba"] = p
            fig_s = px.scatter(
                small,
                x="amount",
                y="fraud_proba",
                color=small["is_fraud"].astype(str),
                labels={"color": "true fraud"},
            )
            st.plotly_chart(fig_s, use_container_width=True)
        except Exception as e:
            st.warning(f"Could not load fraud model: {e}")

with tab_sent:
    st.subheader("Sentiment visualization")
    sent = load_sentiment_results()
    if sent.empty:
        rev = load_reviews_sample(2000)
        st.info("Run `main.py` to materialize sentiment CSV, or showing raw sample only.")
        if not rev.empty:
            st.dataframe(rev.head(20))
    else:
        counts = sent["sentiment"].value_counts().reset_index()
        counts.columns = ["sentiment", "count"]
        fig_pie = px.pie(counts, names="sentiment", values="count", hole=0.35)
        st.plotly_chart(fig_pie, use_container_width=True)
        pol = sent["polarity"]
        fig_hist2 = px.histogram(sent, x="polarity", nbins=40, color="sentiment")
        st.plotly_chart(fig_hist2, use_container_width=True)
        acc = metrics.get("sentiment", {}).get("accuracy_vs_synthetic_labels")
        if acc is not None:
            st.metric("Accuracy vs synthetic labels", f"{acc:.3f}")

with tab_rec:
    st.subheader("Product recommendations (user‑based collaborative filtering)")
    try:
        recs = recommend_for_user(int(user_pick), top_k=top_k)
        if not recs:
            st.warning("User not in training matrix — pick another user_id.")
        else:
            df_r = pd.DataFrame(recs, columns=["product_id", "score"])
            st.dataframe(df_r, use_container_width=True)
            fig_r = px.bar(df_r, x="product_id", y="score", title=f"Top‑{top_k} for user {user_pick}")
            st.plotly_chart(fig_r, use_container_width=True)
    except Exception as e:
        st.error(str(e))

with tab_churn:
    st.subheader("Churn prediction results")
    ch = load_churn_scores()
    if ch.empty:
        st.info("No churn scores CSV.")
    else:
        st.dataframe(ch.head(50), use_container_width=True)
        fig_c = px.histogram(ch, x="churn_proba", color=ch["churned"].astype(str), nbins=40)
        st.plotly_chart(fig_c, use_container_width=True)
        st.metric("Churn model ROC‑AUC", f"{metrics['churn']['roc_auc']:.3f}")

with tab_basket:
    st.subheader("Market basket insights")
    rules = load_rules()
    if rules.empty:
        st.info("No association rules file — run `main.py`.")
    else:
        st.write(f"Showing top rules by lift (total {len(rules)}).")
        show = rules.head(min(25, len(rules)))
        st.dataframe(show, use_container_width=True)
        if "lift" in rules.columns and "confidence" in rules.columns:
            fig_sc = px.scatter(
                rules.head(200),
                x="confidence",
                y="lift",
                size="support",
                hover_data=["antecedents", "consequents"],
            )
            st.plotly_chart(fig_sc, use_container_width=True)

with tab_summary:
    st.subheader("How this maps to Hadoop + Spark")
    st.markdown(
        """
- **`data/`** simulates **HDFS paths** (JSON/CSV as the “lake”). In production, files are
  split into blocks; Spark/Hadoop tasks read **input splits** in parallel.
- **`utils/mapreduce_helpers.py`** shows **map → shuffle → reduce** for per-user fraud rollups.
- **`spark_jobs/batch_processing.py`** runs a **Spark SQL aggregation** when PySpark is installed;
  otherwise it uses **pandas chunked reads** (same logical reduce pattern).
- **Streaming CSVs in `output/`** mimic micro-batch scoring (Spark Structured Streaming mindset).
        """
    )
    st.subheader("Final summary (business view)")
    st.markdown(
        """
**Big Data improves e‑commerce** through personalization (recommendations), fraud prevention
(transaction analytics), retention (churn), and revenue (basket rules, sentiment on reviews).

**Opportunities:** dynamic pricing, targeted campaigns, elastic scale on cloud or on‑prem clusters.

**Challenges:** privacy/compliance, operational complexity, and infrastructure cost.

**Hadoop’s role:** HDFS‑class storage for huge files; MapReduce for batch parallel aggregation;
**Spark** for faster in‑memory pipelines and unified batch + streaming APIs.
        """
    )
    st.text(FINAL_SUMMARY_TEXT)
