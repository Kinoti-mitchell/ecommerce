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
        /* Streamlit 1.32+ maps theme to these; force high contrast so headings/body never go dark-on-dark */
        :root, .stApp, [data-testid="stAppViewContainer"] {
            --st-text-color: #f8fafc !important;
            --st-heading-color: #ffffff !important;
        }
        /* Full-app dark gradient (atmosphere only — main text sits on solid panel below) */
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
            color: #f8fafc !important;
        }
        /* Main column: nearly solid slate (readable text beats heavy frosted gradient bleed) */
        .main .block-container {
            padding-top: 1.75rem;
            padding-bottom: 3rem;
            padding-left: 2rem !important;
            padding-right: 2rem !important;
            max-width: 1180px;
            background: #0f172a !important;
            backdrop-filter: none;
            -webkit-backdrop-filter: none;
            border: 1px solid rgba(125, 211, 252, 0.22);
            border-radius: 18px;
            box-shadow:
                0 4px 24px rgba(0, 0, 0, 0.45),
                inset 0 1px 0 rgba(255, 255, 255, 0.06);
            color: #f8fafc !important;
        }
        /* Headings: .stHeading is what Streamlit uses for st.title / st.subheader (high specificity) */
        .stHeading h1, .stHeading h2, .stHeading h3, .stHeading h4,
        h1, h2, h3, h4,
        [data-testid="stHeader"] h1,
        [data-testid="stHeadingWithActionElements"] h1,
        [data-testid="stHeading"] h1,
        [data-testid="stHeading"] h2,
        [data-testid="stHeading"] h3,
        [data-testid="stMarkdownContainer"] h1 {
            font-weight: 800 !important;
            letter-spacing: -0.02em;
            color: #ffffff !important;
            -webkit-text-fill-color: #ffffff !important;
            background: none !important;
            background-image: none !important;
            background-clip: border-box !important;
            -webkit-background-clip: border-box !important;
            text-shadow: 0 1px 2px rgba(0, 0, 0, 0.85) !important;
        }
        .stHeading h2, .stHeading h3, .stHeading h4,
        h2, h3, h4 {
            font-weight: 600 !important;
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
        h5, h6 {
            color: #f1f5f9 !important;
            text-transform: uppercase;
            letter-spacing: 0.07em;
            font-size: 0.74rem !important;
            font-weight: 700 !important;
        }
        /* Body copy + anything Streamlit renders in the main column */
        section[data-testid="stMain"],
        section[data-testid="stMain"] .stMarkdown {
            color: #f8fafc !important;
        }
        section[data-testid="stMain"] [data-baseweb="typo"],
        .main [data-baseweb="typo"] {
            color: #f8fafc !important;
        }
        .main [data-testid="stMarkdownContainer"] p,
        .main [data-testid="stMarkdownContainer"] li,
        .main [data-testid="stMarkdownContainer"] span,
        section[data-testid="stMain"] p,
        section[data-testid="stMain"] li {
            color: #f8fafc !important;
            line-height: 1.65 !important;
        }
        .main [data-testid="stMarkdownContainer"] strong,
        section[data-testid="stMain"] strong {
            color: #ffffff !important;
            font-weight: 700 !important;
        }
        .main [data-testid="stMarkdownContainer"] a,
        section[data-testid="stMain"] a {
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
        [data-testid="stSidebar"] [data-testid="stCaptionContainer"],
        [data-testid="stSidebar"] [data-baseweb="typo"] {
            color: #f8fafc !important;
        }
        [data-testid="stSidebar"] .stHeading h1,
        [data-testid="stSidebar"] .stHeading h2,
        [data-testid="stSidebar"] .stHeading h3 {
            color: #ffffff !important;
            -webkit-text-fill-color: #ffffff !important;
        }
        [data-testid="stSidebar"] .st-emotion-cache {
            color: inherit;
        }
        /* Expanders — full chrome dark (avoids default light strips on Cloud) */
        div[data-testid="stExpander"] {
            background: rgba(30, 41, 59, 0.92) !important;
            border: 1px solid rgba(56, 189, 248, 0.35);
            border-radius: 12px;
            overflow: hidden;
        }
        div[data-testid="stExpander"] > div {
            background: transparent !important;
        }
        div[data-testid="stExpander"] details {
            border: none;
            border-radius: 0;
            padding: 0.55rem 0.9rem;
            background: transparent !important;
        }
        div[data-testid="stExpander"] summary {
            font-weight: 600 !important;
            color: #ffffff !important;
            background: rgba(15, 23, 42, 0.6) !important;
        }
        div[data-testid="stExpander"] summary:hover {
            background: rgba(51, 65, 85, 0.85) !important;
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
        /* Tabs — inactive tabs were too dim on dark */
        button[data-baseweb="tab"] {
            font-weight: 600 !important;
            color: #e2e8f0 !important;
        }
        button[data-baseweb="tab"][aria-selected="true"] {
            color: #ffffff !important;
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
        /* Plotly embed: avoid white gutter around chart on some hosts */
        [data-testid="stPlotlyChart"],
        [data-testid="stPlotlyChart"] > div,
        .js-plotly-plot .plotly {
            background: transparent !important;
        }
        hr {
            border-color: rgba(148, 163, 184, 0.25) !important;
        }
        .main [data-testid="stCaptionContainer"],
        [data-testid="stCaptionContainer"] {
            color: #f1f5f9 !important;
        }
        [data-testid="stCaptionContainer"] * {
            color: inherit !important;
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
    # Never set title_font_* with title=None — Plotly omits title.text and Plotly.js
    # shows the literal string "undefined" above charts (Streamlit embed).
    fig.update_layout(
        template="plotly_dark",
        font=dict(
            family="'Segoe UI', Inter, system-ui, sans-serif",
            size=14,
            color="#f8fafc",
        ),
        title=dict(text=""),
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
            title=dict(font=dict(color="#f8fafc", size=13)),
            showgrid=True,
            gridcolor="rgba(148, 163, 184, 0.25)",
            zeroline=False,
            tickfont=dict(color="#f1f5f9", size=12),
        ),
        yaxis=dict(
            title=dict(font=dict(color="#f8fafc", size=13)),
            showgrid=True,
            gridcolor="rgba(148, 163, 184, 0.25)",
            zeroline=False,
            tickfont=dict(color="#f1f5f9", size=12),
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
