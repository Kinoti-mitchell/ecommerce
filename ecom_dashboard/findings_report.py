"""Assemble a markdown report of detections and findings from `output/metrics.json`."""

from __future__ import annotations

from datetime import datetime, timezone


def _fmt_pct(x: float | None) -> str:
    if x is None:
        return "—"
    return f"{x * 100:.1f}%"


def _fmt_float(x: float | None, nd: int = 3) -> str:
    if x is None:
        return "—"
    return f"{x:.{nd}f}"


def build_findings_report_markdown(metrics: dict) -> str:
    """Human-readable report for instructors / stakeholders (also downloadable)."""
    now = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")
    lines: list[str] = [
        "# Detections & findings report",
        "",
        f"*Generated: {now}*",
        "",
        "## 1. Pipeline run",
        "",
    ]

    mode = metrics.get("pipeline_mode", "unknown")
    lines.append(f"- **Mode:** `{mode}` (full = larger synthetic lake; quick = faster hosted runs).")
    dl = metrics.get("data_lake") or {}
    lines.append(f"- **Transactions in lake:** {dl.get('transactions_rows', '—')}")
    lines.append(f"- **MapReduce user rollups:** {metrics.get('mapreduce_rollup_users', '—')} users aggregated.")
    spark_p = dl.get("spark_summary_path")
    if spark_p:
        lines.append(f"- **Spark / batch summary artifact:** `{spark_p}`")
    lines.append("")

    lines += [
        "## 2. Fraud detection (supervised)",
        "",
        "Random Forest on engineered behaviour features vs amount-only baseline.",
        "",
    ]
    fc = metrics.get("fraud_model_clean") or {}
    fb = metrics.get("fraud_model_dirty_baseline") or {}
    roc_c = fc.get("roc_auc")
    roc_b = fb.get("roc_auc")
    lines.append(f"| Model | ROC-AUC | Accuracy |")
    lines.append(f"| --- | ---: | ---: |")
    lines.append(f"| Full (clean + features) | {_fmt_float(roc_c)} | {_fmt_float(fc.get('accuracy'))} |")
    lines.append(f"| Baseline (amount only) | {_fmt_float(roc_b)} | {_fmt_float(fb.get('accuracy'))} |")
    lines.append("")
    if roc_c is not None and roc_b is not None:
        if roc_c > roc_b:
            lines.append(
                "**Finding:** The full pipeline achieves a higher ROC-AUC than the baseline, "
                "supporting the value of cleaning and feature engineering for fraud ranking."
            )
        elif roc_c < roc_b:
            lines.append(
                "**Finding:** On this synthetic slice, the baseline ROC-AUC is higher—"
                "worth investigating class balance, leakage, or random variation; "
                "the dashboard still contrasts both setups for teaching."
            )
        else:
            lines.append("**Finding:** Full and baseline ROC-AUC are tied on this run.")
    note = metrics.get("preprocessing_note")
    if note:
        lines += ["", f"*Note:* {note}", ""]
    lines.append("")

    anom = metrics.get("transaction_anomalies")
    lines += [
        "## 3. Unsupervised transaction anomalies",
        "",
        "Isolation Forest on behaviour features **without** using the fraud label for training.",
        "",
    ]
    if anom:
        lines.append(f"- **Rows scored:** {anom.get('n_rows', '—')}")
        lines.append(f"- **Trees / estimators:** {anom.get('n_estimators', '—')}")
        lines.append(f"- **Expected contamination:** {_fmt_float(anom.get('contamination'), 2)}")
        lines.append(f"- **Rows flagged as outliers:** {anom.get('n_flagged_outliers', '—')}")
        ov = anom.get("top_100_overlap_with_labeled_fraud")
        if ov is not None:
            lines.append(
                f"- **Labeled fraud among top 100 anomaly scores:** {_fmt_pct(ov)} *(diagnostic only)*"
            )
        feats = anom.get("feature_cols")
        if feats:
            lines.append(f"- **Features:** {', '.join(feats)}")
        lines += [
            "",
            "**Finding:** High anomaly scores highlight rare combinations in the feature space; "
            "they are not the same as supervised fraud probability and should be triaged separately.",
            "",
        ]
    else:
        lines.append("*No anomaly metrics in this `metrics.json` — re-run the pipeline after upgrading.*")
        lines.append("")

    sent = metrics.get("sentiment") or {}
    lines += [
        "## 4. Review sentiment",
        "",
    ]
    lines.append(f"- **Reviews scored:** {sent.get('n_reviews', '—')}")
    acc = sent.get("accuracy_vs_synthetic_labels")
    if acc is not None:
        lines.append(f"- **Accuracy vs synthetic labels:** {_fmt_float(acc)}")
        lines.append(
            "**Finding:** TextBlob polarity labels are checked against demo `true_sentiment` where present."
        )
    lines.append("")

    churn = metrics.get("churn") or {}
    lines += [
        "## 5. Churn prediction",
        "",
        f"- **ROC-AUC:** {_fmt_float(churn.get('roc_auc'))}",
        f"- **Accuracy:** {_fmt_float(churn.get('accuracy'))}",
        "",
        "**Finding:** Gradient boosting ranks users by churn risk using tenure, spend, sessions, and support load.",
        "",
    ]

    mb = metrics.get("market_basket") or {}
    cf = metrics.get("collaborative_filtering") or {}
    lines += [
        "## 6. Market basket & recommendations",
        "",
        f"- **Association rules mined:** {mb.get('n_rules', '—')}",
        f"- **Frequent itemsets:** {mb.get('n_frequent_itemsets', '—')}",
        f"- **Collaborative filtering matrix:** {cf.get('n_users_in_matrix', '—')} users × "
        f"{cf.get('n_products_in_matrix', '—')} products",
        "",
        "**Finding:** Basket rules support cross-sell insights; CF supports product suggestions from rating similarity.",
        "",
    ]

    lines += [
        "## 7. Output artifacts (for audit)",
        "",
        "| Area | Typical paths |",
        "| --- | --- |",
        "| Metrics | `output/metrics.json` |",
        "| Fraud scores | `output/fraud_scored_transactions.csv` |",
        "| Anomaly ranks | `output/transaction_anomalies_top500.csv` |",
        "| Churn scores | `output/churn_scores.csv` |",
        "| Sentiment | `output/sentiment_reviews.csv` |",
        "| Basket rules | `output/association_rules.csv` |",
        "",
        "---",
        "*End of report.*",
    ]

    return "\n".join(lines)
