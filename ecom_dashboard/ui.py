"""Shared UI helpers: CSS and Plotly polish for Streamlit (readable dark theme)."""

from __future__ import annotations

from typing import Any

FRAUD_COLORS = {"0": "#2dd4bf", "1": "#fb7185"}
SENTIMENT_COLORS = {
    "positive": "#4ade80",
    "negative": "#f87171",
    "neutral": "#cbd5e1",
}


def inject_custom_css() -> None:
    import streamlit as st

    st.markdown(
        """
        <style>
        /* Main column */
        .main .block-container {
            padding-top: 1.5rem;
            padding-bottom: 3rem;
            max-width: 1180px;
        }
        /* Title: solid high-contrast (gradient clip often fails → invisible text) */
        h1 {
            font-weight: 800 !important;
            letter-spacing: -0.02em;
            color: #f8fafc !important;
            -webkit-text-fill-color: #f8fafc !important;
            background: none !important;
            text-shadow: 0 1px 2px rgba(0,0,0,0.45);
        }
        h2, h3 {
            color: #f1f5f9 !important;
            font-weight: 600 !important;
        }
        h5, h6 {
            color: #cbd5e1 !important;
            text-transform: uppercase;
            letter-spacing: 0.06em;
            font-size: 0.72rem !important;
            font-weight: 700 !important;
        }
        /* Body markdown in main area */
        .main [data-testid="stMarkdownContainer"] p,
        .main [data-testid="stMarkdownContainer"] li,
        .main [data-testid="stMarkdownContainer"] span {
            color: #e2e8f0 !important;
        }
        .main [data-testid="stMarkdownContainer"] strong {
            color: #f8fafc !important;
        }
        .main [data-testid="stMarkdownContainer"] a {
            color: #7dd3fc !important;
        }
        /* Expanders */
        div[data-testid="stExpander"] details {
            border: 1px solid rgba(56, 189, 248, 0.35);
            border-radius: 12px;
            padding: 0.5rem 0.85rem;
            background: #243047 !important;
        }
        div[data-testid="stExpander"] summary {
            font-weight: 600 !important;
            color: #f1f5f9 !important;
        }
        div[data-testid="stExpander"] [data-testid="stMarkdownContainer"] p,
        div[data-testid="stExpander"] [data-testid="stMarkdownContainer"] li {
            color: #e2e8f0 !important;
        }
        /* Alerts: never white box / white text */
        div[data-testid="stAlert"] {
            background-color: #243047 !important;
            border: 1px solid #3d4f66 !important;
            color: #f1f5f9 !important;
        }
        div[data-testid="stAlert"] p,
        div[data-testid="stAlert"] span,
        div[data-testid="stAlert"] div {
            color: #f1f5f9 !important;
        }
        div[data-testid="stAlert"] a {
            color: #7dd3fc !important;
        }
        /* Status / success messages */
        div[data-testid="stSuccess"] {
            background-color: #14532d !important;
            border: 1px solid #166534 !important;
        }
        div[data-testid="stSuccess"] p,
        div[data-testid="stSuccess"] span {
            color: #ecfdf5 !important;
        }
        /* Sidebar: labels + text */
        [data-testid="stSidebar"] [data-testid="stMarkdownContainer"] p,
        [data-testid="stSidebar"] label,
        [data-testid="stSidebar"] .stMarkdown {
            color: #e2e8f0 !important;
        }
        [data-testid="stSidebar"] .st-emotion-cache {
            color: inherit;
        }
        /* Tabs */
        button[data-baseweb="tab"] {
            font-weight: 600 !important;
            color: #94a3b8 !important;
        }
        button[data-baseweb="tab"][aria-selected="true"] {
            color: #38bdf8 !important;
        }
        /* Metrics */
        div[data-testid="metric-container"] {
            background: #243047 !important;
            border: 1px solid #3d4f66 !important;
            border-radius: 12px;
            padding: 0.75rem 1rem;
        }
        [data-testid="stMetricValue"] {
            color: #f8fafc !important;
        }
        [data-testid="stMetricLabel"] {
            color: #cbd5e1 !important;
        }
        [data-testid="stMetricDelta"] {
            color: #94a3b8 !important;
        }
        /* Dataframes */
        div[data-testid="stDataFrame"] {
            border-radius: 10px;
            border: 1px solid #3d4f66;
        }
        hr {
            border-color: #3d4f66 !important;
        }
        [data-testid="stCaptionContainer"] {
            color: #94a3b8 !important;
        }
        /* Plain text blocks (e.g. summary expander) */
        pre, .stCodeBlock, [data-testid="stCode"] {
            background-color: #0f172a !important;
            color: #e2e8f0 !important;
            border: 1px solid #334155 !important;
            border-radius: 8px !important;
        }
        /* Inputs in sidebar */
        [data-testid="stSidebar"] .stNumberInput label,
        [data-testid="stSidebar"] .stSlider label {
            color: #e2e8f0 !important;
        }
        </style>
        """,
        unsafe_allow_html=True,
    )


def polish_fig(
    fig: Any,
    *,
    x_title: str | None = None,
    y_title: str | None = None,
) -> Any:
    """Dark chart surface matching the app (no white plot area)."""
    fig.update_layout(
        template="plotly_dark",
        font=dict(
            family="'Segoe UI', Inter, system-ui, sans-serif",
            size=13,
            color="#e2e8f0",
        ),
        title=None,
        title_font_size=14,
        title_font_color="#f8fafc",
        margin=dict(l=12, r=12, t=28, b=12),
        paper_bgcolor="#1e293b",
        plot_bgcolor="#1e293b",
        legend=dict(
            orientation="h",
            yanchor="bottom",
            y=1.02,
            xanchor="right",
            x=1,
            bgcolor="rgba(30, 41, 59, 0.95)",
            font=dict(color="#f1f5f9", size=12),
            title_font_color="#f1f5f9",
        ),
        xaxis=dict(
            title=dict(font=dict(color="#cbd5e1")),
            showgrid=True,
            gridcolor="rgba(148, 163, 184, 0.2)",
            zeroline=False,
            tickfont=dict(color="#cbd5e1"),
        ),
        yaxis=dict(
            title=dict(font=dict(color="#cbd5e1")),
            showgrid=True,
            gridcolor="rgba(148, 163, 184, 0.2)",
            zeroline=False,
            tickfont=dict(color="#cbd5e1"),
        ),
    )
    if x_title:
        fig.update_layout(xaxis_title=x_title)
    if y_title:
        fig.update_layout(yaxis_title=y_title)
    return fig


def plotly_config() -> dict:
    return {
        "displayModeBar": True,
        "displaylogo": False,
        "modeBarButtonsToRemove": ["lasso2d", "select2d"],
        "toImageButtonOptions": {"format": "png", "scale": 2},
    }
