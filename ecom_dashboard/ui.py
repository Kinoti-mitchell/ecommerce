"""Shared UI helpers: dark gradient atmosphere + high-contrast readable text."""

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
        /* Full-app dark gradient (atmosphere) */
        .stApp,
        [data-testid="stAppViewContainer"] {
            background: linear-gradient(
                165deg,
                #0a0e17 0%,
                #0f172a 25%,
                #134e4a 55%,
                #1e1b4b 78%,
                #0f172a 100%
            ) !important;
            background-attachment: fixed !important;
        }
        /* Main column: frosted panel so ALL text reads clearly on top of gradient */
        .main .block-container {
            padding-top: 1.75rem;
            padding-bottom: 3rem;
            padding-left: 2rem !important;
            padding-right: 2rem !important;
            max-width: 1180px;
            background: rgba(15, 23, 42, 0.92) !important;
            backdrop-filter: blur(14px);
            -webkit-backdrop-filter: blur(14px);
            border: 1px solid rgba(125, 211, 252, 0.18);
            border-radius: 18px;
            box-shadow:
                0 4px 24px rgba(0, 0, 0, 0.45),
                inset 0 1px 0 rgba(255, 255, 255, 0.06);
        }
        /* Title: always solid light text (never gradient-fill on text) */
        h1 {
            font-weight: 800 !important;
            letter-spacing: -0.02em;
            color: #ffffff !important;
            -webkit-text-fill-color: #ffffff !important;
            background: none !important;
            text-shadow:
                0 0 20px rgba(15, 23, 42, 0.9),
                0 2px 4px rgba(0, 0, 0, 0.5);
        }
        /* Gradient accent bar under title (pretty + no readability issue) */
        h1::after {
            content: "";
            display: block;
            height: 4px;
            width: min(200px, 40vw);
            margin-top: 0.65rem;
            border-radius: 4px;
            background: linear-gradient(90deg, #22d3ee, #818cf8, #c084fc);
            box-shadow: 0 0 16px rgba(34, 211, 238, 0.35);
        }
        h2, h3 {
            color: #ffffff !important;
            font-weight: 600 !important;
            text-shadow: 0 1px 3px rgba(0, 0, 0, 0.4);
        }
        h5, h6 {
            color: #e2e8f0 !important;
            text-transform: uppercase;
            letter-spacing: 0.07em;
            font-size: 0.74rem !important;
            font-weight: 700 !important;
        }
        /* Body copy: maximum readability */
        .main [data-testid="stMarkdownContainer"] p,
        .main [data-testid="stMarkdownContainer"] li,
        .main [data-testid="stMarkdownContainer"] span {
            color: #f1f5f9 !important;
            line-height: 1.65 !important;
        }
        .main [data-testid="stMarkdownContainer"] strong {
            color: #ffffff !important;
        }
        .main [data-testid="stMarkdownContainer"] a {
            color: #7dd3fc !important;
            font-weight: 500;
        }
        /* Sidebar: matching gradient strip */
        [data-testid="stSidebar"] {
            background: linear-gradient(
                180deg,
                #0c1220 0%,
                #0f172a 40%,
                #172554 100%
            ) !important;
            border-right: 1px solid rgba(56, 189, 248, 0.15) !important;
        }
        [data-testid="stSidebar"] > div:first-child {
            background: transparent !important;
        }
        [data-testid="stSidebar"] [data-testid="stMarkdownContainer"] p,
        [data-testid="stSidebar"] label,
        [data-testid="stSidebar"] .stMarkdown,
        [data-testid="stSidebar"] [data-testid="stCaptionContainer"] {
            color: #f1f5f9 !important;
        }
        [data-testid="stSidebar"] .st-emotion-cache {
            color: inherit;
        }
        /* Expanders */
        div[data-testid="stExpander"] details {
            border: 1px solid rgba(56, 189, 248, 0.35);
            border-radius: 12px;
            padding: 0.55rem 0.9rem;
            background: rgba(30, 41, 59, 0.95) !important;
        }
        div[data-testid="stExpander"] summary {
            font-weight: 600 !important;
            color: #ffffff !important;
        }
        div[data-testid="stExpander"] [data-testid="stMarkdownContainer"] p,
        div[data-testid="stExpander"] [data-testid="stMarkdownContainer"] li {
            color: #f1f5f9 !important;
        }
        /* Alerts */
        div[data-testid="stAlert"] {
            background-color: rgba(30, 41, 59, 0.98) !important;
            border: 1px solid rgba(125, 211, 252, 0.25) !important;
        }
        div[data-testid="stAlert"] p,
        div[data-testid="stAlert"] span,
        div[data-testid="stAlert"] div {
            color: #f8fafc !important;
        }
        div[data-testid="stAlert"] a {
            color: #7dd3fc !important;
        }
        div[data-testid="stSuccess"] {
            background-color: rgba(21, 87, 36, 0.95) !important;
            border: 1px solid #22c55e !important;
        }
        div[data-testid="stSuccess"] p,
        div[data-testid="stSuccess"] span {
            color: #f0fdf4 !important;
        }
        /* Tabs */
        button[data-baseweb="tab"] {
            font-weight: 600 !important;
            color: #cbd5e1 !important;
        }
        button[data-baseweb="tab"][aria-selected="true"] {
            color: #38bdf8 !important;
        }
        /* Metrics */
        div[data-testid="metric-container"] {
            background: rgba(30, 41, 59, 0.9) !important;
            border: 1px solid rgba(125, 211, 252, 0.2) !important;
            border-radius: 12px;
            padding: 0.85rem 1rem;
        }
        [data-testid="stMetricValue"] {
            color: #ffffff !important;
        }
        [data-testid="stMetricLabel"] {
            color: #e2e8f0 !important;
        }
        [data-testid="stMetricDelta"] {
            color: #cbd5e1 !important;
        }
        div[data-testid="stDataFrame"] {
            border-radius: 10px;
            border: 1px solid rgba(125, 211, 252, 0.2);
        }
        hr {
            border-color: rgba(148, 163, 184, 0.25) !important;
        }
        /* Captions: brighter than before so they read on gradient edges */
        .main [data-testid="stCaptionContainer"],
        [data-testid="stCaptionContainer"] {
            color: #e2e8f0 !important;
        }
        pre, .stCodeBlock, [data-testid="stCode"] {
            background-color: #0f172a !important;
            color: #f1f5f9 !important;
            border: 1px solid rgba(125, 211, 252, 0.2) !important;
            border-radius: 8px !important;
        }
        [data-testid="stSidebar"] .stNumberInput label,
        [data-testid="stSidebar"] .stSlider label {
            color: #f1f5f9 !important;
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
    """Chart surface aligned with frosted panel (slate, not white)."""
    fig.update_layout(
        template="plotly_dark",
        font=dict(
            family="'Segoe UI', Inter, system-ui, sans-serif",
            size=13,
            color="#f1f5f9",
        ),
        title=None,
        title_font_size=14,
        title_font_color="#ffffff",
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
            font=dict(color="#f8fafc", size=12),
            title_font_color="#f8fafc",
        ),
        xaxis=dict(
            title=dict(font=dict(color="#e2e8f0")),
            showgrid=True,
            gridcolor="rgba(148, 163, 184, 0.2)",
            zeroline=False,
            tickfont=dict(color="#e2e8f0"),
        ),
        yaxis=dict(
            title=dict(font=dict(color="#e2e8f0")),
            showgrid=True,
            gridcolor="rgba(148, 163, 184, 0.2)",
            zeroline=False,
            tickfont=dict(color="#e2e8f0"),
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
