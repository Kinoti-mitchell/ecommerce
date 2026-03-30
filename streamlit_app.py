"""
Streamlit dashboard for the e-commerce Big Data analytics demo.

Run:
    streamlit run streamlit_app.py

If `output/metrics.json` is missing (e.g. fresh clone or Streamlit Cloud), the app
runs `main.main()` once on first load to generate `data/`, `models/`, and `output/`.
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

import config

from analytics.fraud import engineer_fraud_features, load_fraud_artifacts
from analytics.recommendations import recommend_for_user
from ecom_dashboard import explanations as explain
from ecom_dashboard import ui as ui_theme
from ecom_dashboard.loaders import (
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
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded",
)

px.defaults.template = "plotly_dark"
ui_theme.inject_custom_css()

_METRICS_PATH = config.OUTPUT_DIR / "metrics.json"
_PLOT_CFG = ui_theme.plotly_config()


def _run_batch_pipeline_if_needed() -> None:
    """Hosted apps (Streamlit Cloud) do not run main.py; generate artifacts on first open."""
    if _METRICS_PATH.exists():
        return
    st.title("E‑commerce Big Data Analytics Lab")
    st.caption(
        "Simulated data lake (HDFS-style `data/`), MapReduce-style rollups, optional PySpark, and Streamlit."
    )
    st.info(
        "**First load:** generating the synthetic data lake, training models, and writing "
        "`output/metrics.json`. This can take **2–8 minutes** on free hosting—please wait. "
        "Tip: set secrets env **`STREAMLIT_QUICK=1`** for smaller data and faster cold starts."
    )
    with st.status("Running batch pipeline (`main.py`)…", expanded=True) as status:
        try:
            import main as pipeline_main

            pipeline_main.main()
            status.update(label="Pipeline finished.", state="complete")
        except Exception as e:
            status.update(label="Pipeline failed.", state="error")
            st.error(
                "The batch pipeline failed. On **Streamlit Cloud**, try redeploying or run "
                "`python main.py` locally and commit `output/metrics.json` if your course allows it."
            )
            st.exception(e)
            st.stop()
    if not _METRICS_PATH.exists():
        st.error("`main.py` finished but `output/metrics.json` was not created.")
        st.stop()
    st.rerun()


_run_batch_pipeline_if_needed()

st.title("E‑commerce Big Data Analytics Lab")
st.caption(
    "Simulated data lake (HDFS-style `data/`), MapReduce-style rollups, optional PySpark, and Streamlit."
)
with st.expander("What does this system do? (short overview)", expanded=False):
    st.markdown(explain.SYSTEM_OVERVIEW)

metrics = load_metrics()
if not metrics:
    st.error(
        "`output/metrics.json` is still missing after the pipeline. "
        "Check logs or run `python main.py` locally."
    )
    st.stop()

# --- Hero KPI strip ---
st.markdown("##### At a glance")
k1, k2, k3, k4 = st.columns(4)
with k1:
    st.metric(
        "Fraud ROC‑AUC (full)",
        f"{metrics['fraud_model_clean']['roc_auc']:.3f}",
        help="Higher = better separation of fraud vs normal transactions",
    )
with k2:
    st.metric(
        "Fraud baseline",
        f"{metrics['fraud_model_dirty_baseline']['roc_auc']:.3f}",
        help="Amount-only model (no engineered features)",
    )
with k3:
    st.metric(
        "Churn ROC‑AUC",
        f"{metrics['churn']['roc_auc']:.3f}",
        help="Churn vs retained users",
    )
with k4:
    _sacc = metrics.get("sentiment", {}).get("accuracy_vs_synthetic_labels")
    st.metric(
        "Sentiment accuracy",
        f"{_sacc:.3f}" if _sacc is not None else "—",
        help="Vs synthetic labels in demo data",
    )
st.divider()

# --- Sidebar ---
st.sidebar.markdown("### Controls")
st.sidebar.caption("Adjust what you see in the tabs below.")
user_pick = st.sidebar.number_input("User ID (recommendations)", min_value=1, value=1, step=1)
top_k = st.sidebar.slider("Top‑K products", 3, 15, 6)
fraud_sample_n = st.sidebar.slider("Fraud chart sample size", 1000, 15000, 6000)

st.sidebar.divider()
st.sidebar.markdown("### Model snapshot")
if metrics.get("pipeline_mode"):
    st.sidebar.success(f"Pipeline: **{metrics['pipeline_mode']}**")
st.sidebar.metric("Fraud ROC‑AUC (full)", f"{metrics['fraud_model_clean']['roc_auc']:.3f}")
st.sidebar.metric("Fraud ROC‑AUC (baseline)", f"{metrics['fraud_model_dirty_baseline']['roc_auc']:.3f}")
st.sidebar.metric("Churn ROC‑AUC", f"{metrics['churn']['roc_auc']:.3f}")
with st.sidebar.expander("What do these metrics mean?"):
    st.markdown(explain.SIDEBAR_METRICS)

# --- Tabs ---
tab_fraud, tab_sent, tab_rec, tab_churn, tab_basket, tab_summary = st.tabs(
    [
        "Fraud",
        "Sentiment",
        "Recommendations",
        "Churn",
        "Market basket",
        "Big Data summary",
    ]
)

with tab_fraud:
    st.subheader("Fraud detection")
    with st.expander("What this tab shows", expanded=False):
        st.markdown(explain.TAB_FRAUD)
    tx = load_transactions_sample(fraud_sample_n)
    if tx.empty:
        st.info("No transaction data — run the batch pipeline first.")
    else:
        c1, c2 = st.columns(2, gap="medium")
        with c1:
            st.markdown("**Amount distribution**")
            tx_vis = tx.copy()
            tx_vis["is_fraud"] = tx_vis["is_fraud"].astype(str).replace({"0": "No", "1": "Yes"})
            fig_hist = px.histogram(
                tx_vis,
                x="amount",
                nbins=60,
                color="is_fraud",
                barmode="overlay",
                opacity=0.75,
                color_discrete_map={"No": ui_theme.FRAUD_COLORS["0"], "Yes": ui_theme.FRAUD_COLORS["1"]},
            )
            fig_hist.update_layout(legend_title_text="Fraud")
            st.plotly_chart(
                ui_theme.polish_fig(fig_hist),
                use_container_width=True,
                config=_PLOT_CFG,
            )
        with c2:
            st.markdown("**Fraud rate by amount decile**")
            tx2 = tx.copy()
            tx2["decile"] = pd.qcut(tx2["amount"], q=10, labels=False, duplicates="drop")
            rate = tx2.groupby("decile", observed=True)["is_fraud"].mean().reset_index()
            fig_bar = px.bar(
                rate,
                x="decile",
                y="is_fraud",
                labels={"is_fraud": "Fraud rate", "decile": "Decile"},
                color="is_fraud",
                color_continuous_scale="Reds",
            )
            fig_bar.update_layout(showlegend=False)
            st.plotly_chart(
                ui_theme.polish_fig(fig_bar),
                use_container_width=True,
                config=_PLOT_CFG,
            )

        st.divider()
        st.markdown("**Feature + cleaning impact**")
        fc = metrics["fraud_model_clean"]
        fd = metrics["fraud_model_dirty_baseline"]
        comp = pd.DataFrame(
            {
                "Pipeline": ["Full (clean + features)", "Baseline (amount only)"],
                "ROC‑AUC": [fc["roc_auc"], fd["roc_auc"]],
                "Accuracy": [fc["accuracy"], fd["accuracy"]],
            }
        )
        c3, c4 = st.columns((1, 2), gap="medium")
        with c3:
            st.dataframe(comp, use_container_width=True, hide_index=True)
        with c4:
            fig_cmp = px.bar(
                comp,
                x="Pipeline",
                y="ROC‑AUC",
                color="Pipeline",
                text_auto=".3f",
                color_discrete_sequence=["#22d3ee", "#64748b"],
            )
            fig_cmp.update_layout(showlegend=False, yaxis_range=[0, 1.05])
            st.plotly_chart(
                ui_theme.polish_fig(fig_cmp),
                use_container_width=True,
                config=_PLOT_CFG,
            )

        st.divider()
        st.markdown("**Scored sample (model probability vs amount)**")
        try:
            clf, cols = load_fraud_artifacts("fraud_rf")
            small = tx.head(200).copy()
            xf = engineer_fraud_features(small)
            p = clf.predict_proba(xf[cols].fillna(0))[:, 1]
            small = small.reset_index(drop=True)
            small["fraud_proba"] = p
            small["Actual fraud"] = small["is_fraud"].astype(str).replace({"0": "No", "1": "Yes"})
            fig_s = px.scatter(
                small,
                x="amount",
                y="fraud_proba",
                color="Actual fraud",
                color_discrete_map={"No": ui_theme.FRAUD_COLORS["0"], "Yes": ui_theme.FRAUD_COLORS["1"]},
                labels={"fraud_proba": "Fraud probability"},
            )
            st.plotly_chart(
                ui_theme.polish_fig(fig_s),
                use_container_width=True,
                config=_PLOT_CFG,
            )
        except Exception as e:
            st.warning(f"Could not load fraud model: {e}")

with tab_sent:
    st.subheader("Review sentiment")
    with st.expander("What this tab shows", expanded=False):
        st.markdown(explain.TAB_SENTIMENT)
    sent = load_sentiment_results()
    if sent.empty:
        rev = load_reviews_sample(2000)
        st.info("Run `main.py` to build sentiment scores, or browse a raw sample below.")
        if not rev.empty:
            st.dataframe(rev.head(20), use_container_width=True, hide_index=True)
    else:
        c1, c2 = st.columns(2, gap="medium")
        with c1:
            counts = sent["sentiment"].value_counts().reset_index()
            counts.columns = ["sentiment", "count"]
            fig_pie = px.pie(
                counts,
                names="sentiment",
                values="count",
                hole=0.4,
                color="sentiment",
                color_discrete_map=ui_theme.SENTIMENT_COLORS,
            )
            st.plotly_chart(
                ui_theme.polish_fig(fig_pie),
                use_container_width=True,
                config=_PLOT_CFG,
            )
        with c2:
            fig_hist2 = px.histogram(
                sent,
                x="polarity",
                nbins=40,
                color="sentiment",
                color_discrete_map=ui_theme.SENTIMENT_COLORS,
                labels={"polarity": "Polarity", "count": "Reviews"},
            )
            st.plotly_chart(
                ui_theme.polish_fig(fig_hist2),
                use_container_width=True,
                config=_PLOT_CFG,
            )
        acc = metrics.get("sentiment", {}).get("accuracy_vs_synthetic_labels")
        if acc is not None:
            st.metric("Accuracy vs synthetic labels", f"{acc * 100:.1f}%")

with tab_rec:
    st.subheader("Recommendations")
    with st.expander("What this tab shows", expanded=False):
        st.markdown(explain.TAB_RECOMMENDATIONS)
    try:
        recs = recommend_for_user(int(user_pick), top_k=top_k)
        if not recs:
            st.warning("That user isn’t in the training matrix — try another **User ID** in the sidebar.")
        else:
            df_r = pd.DataFrame(recs, columns=["product_id", "score"])
            df_r["score"] = df_r["score"].round(4)
            st.dataframe(df_r, use_container_width=True, hide_index=True)
            fig_r = px.bar(
                df_r,
                x="product_id",
                y="score",
                text_auto=".3f",
                color="score",
                color_continuous_scale="PuBu",
                labels={"score": "Score", "product_id": "Product"},
            )
            fig_r.update_layout(showlegend=False)
            st.plotly_chart(
                ui_theme.polish_fig(fig_r),
                use_container_width=True,
                config=_PLOT_CFG,
            )
    except Exception as e:
        st.error(str(e))

with tab_churn:
    st.subheader("Churn risk")
    with st.expander("What this tab shows", expanded=False):
        st.markdown(explain.TAB_CHURN)
    ch = load_churn_scores()
    if ch.empty:
        st.info("No churn scores — run the batch pipeline first.")
    else:
        st.dataframe(ch.head(50), use_container_width=True, hide_index=True)
        ch_vis = ch.copy()
        ch_vis["Churned (actual)"] = ch_vis["churned"].astype(str).replace({"0": "No", "1": "Yes"})
        fig_c = px.histogram(
            ch_vis,
            x="churn_proba",
            color="Churned (actual)",
            nbins=40,
            barmode="overlay",
            opacity=0.65,
            color_discrete_map={"No": ui_theme.FRAUD_COLORS["0"], "Yes": ui_theme.FRAUD_COLORS["1"]},
            labels={"churn_proba": "Predicted churn probability"},
        )
        st.plotly_chart(
            ui_theme.polish_fig(fig_c),
            use_container_width=True,
            config=_PLOT_CFG,
        )
        st.metric("Churn model ROC‑AUC", f"{metrics['churn']['roc_auc']:.3f}")

with tab_basket:
    st.subheader("Market basket")
    with st.expander("What this tab shows", expanded=False):
        st.markdown(explain.TAB_BASKET)
    rules = load_rules()
    if rules.empty:
        st.info("No association rules — run `main.py` to mine baskets.")
    else:
        st.caption(f"{len(rules)} rules · showing top 25 by lift")
        show = rules.head(min(25, len(rules)))
        st.dataframe(show, use_container_width=True, hide_index=True)
        if "lift" in rules.columns and "confidence" in rules.columns:
            fig_sc = px.scatter(
                rules.head(200),
                x="confidence",
                y="lift",
                size="support",
                hover_data=["antecedents", "consequents"],
                color="lift",
                color_continuous_scale="Viridis",
                labels={"confidence": "Confidence", "lift": "Lift"},
            )
            st.plotly_chart(
                ui_theme.polish_fig(fig_sc),
                use_container_width=True,
                config=_PLOT_CFG,
            )

with tab_summary:
    st.subheader("Hadoop · Spark · business context")
    with st.expander("What this tab shows", expanded=False):
        st.markdown(explain.TAB_SUMMARY)
    st.markdown(
        """
- **`data/`** — simulated **HDFS-style** lake (CSV/JSON). In production, files are split into blocks;
  jobs read **splits** in parallel.
- **`utils/mapreduce_helpers.py`** — **map → shuffle → reduce** (e.g. per-user fraud rollups).
- **`spark_jobs/batch_processing.py`** — **Spark SQL** aggregation when PySpark is on; else **pandas chunks**
  (same reduce idea).
- **`output/` streaming CSVs** — micro-batch style scoring (similar mindset to Spark Structured Streaming).
        """
    )
    st.divider()
    st.markdown("**Business view**")
    st.markdown(
        """
**Big Data** supports personalization, fraud prevention, retention, and revenue (baskets + sentiment).

**Opportunities:** dynamic pricing, campaigns, elastic scale.

**Challenges:** privacy, complexity, cost.

**Hadoop ecosystem:** HDFS-class storage; MapReduce for batch aggregation; **Spark** for faster analytics & streaming APIs.
        """
    )
    with st.expander("Full learner summary (text)"):
        st.text(FINAL_SUMMARY_TEXT)

st.divider()
st.caption(
    "E‑commerce Big Data analytics demo · synthetic data only · "
    "[GitHub](https://github.com/Kinoti-mitchell/ecommerce)"
)
