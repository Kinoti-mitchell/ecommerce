"""Shared UI helpers: CSS and Plotly polish for Streamlit (dark theme)."""

from __future__ import annotations

from typing import Any

# Brighter series colors for dark UI backgrounds
FRAUD_COLORS = {"0": "#2dd4bf", "1": "#fb7185"}
SENTIMENT_COLORS = {
    "positive": "#4ade80",
    "negative": "#f87171",
    "neutral": "#94a3b8",
}


def inject_custom_css() -> None:
    import streamlit as st

    st.markdown(
        """
        <style>
        /* Subtle depth behind main column */
        .main .block-container {
            padding-top: 1.5rem;
            padding-bottom: 3rem;
            max-width: 1180px;
        }
        /* Hero title */
        h1 {
            font-weight: 800 !important;
            letter-spacing: -0.03em;
            background: linear-gradient(120deg, #e0f2fe 0%, #22d3ee 45%, #a78bfa 100%);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
            background-clip: text;
        }
        h2, h3 {
            color: #f1f5f9 !important;
            font-weight: 600 !important;
        }
        /* Section label (#####) */
        h5, h6 {
            color: #94a3b8 !important;
            text-transform: uppercase;
            letter-spacing: 0.06em;
            font-size: 0.72rem !important;
            font-weight: 700 !important;
        }
        /* Expanders: glass cards */
        div[data-testid="stExpander"] details {
            border: 1px solid rgba(34, 211, 238, 0.25);
            border-radius: 14px;
            padding: 0.4rem 0.75rem;
            background: linear-gradient(
                145deg,
                rgba(30, 41, 59, 0.85) 0%,
                rgba(15, 23, 42, 0.65) 100%
            );
            box-shadow: 0 4px 24px rgba(0, 0, 0, 0.35);
        }
        div[data-testid="stExpander"] summary {
            font-weight: 600 !important;
            color: #cbd5e1 !important;
        }
        /* Tabs: clearer active state */
        button[data-baseweb="tab"] {
            font-weight: 600 !important;
            border-radius: 8px 8px 0 0 !important;
        }
        button[data-baseweb="tab"][aria-selected="true"] {
            color: #22d3ee !important;
            border-bottom: 2px solid #22d3ee !important;
        }
        /* KPI metrics: glass strip */
        div[data-testid="metric-container"] {
            background: linear-gradient(
                135deg,
                rgba(34, 211, 238, 0.12) 0%,
                rgba(167, 139, 250, 0.08) 100%
            );
            border: 1px solid rgba(148, 163, 184, 0.2);
            border-radius: 12px;
            padding: 0.75rem 1rem;
        }
        [data-testid="stMetricValue"] {
            color: #f8fafc !important;
        }
        [data-testid="stMetricLabel"] {
            color: #94a3b8 !important;
        }
        /* Dataframes */
        div[data-testid="stDataFrame"] {
            border-radius: 10px;
            overflow: hidden;
            border: 1px solid rgba(148, 163, 184, 0.15);
        }
        /* Dividers */
        hr {
            border-color: rgba(148, 163, 184, 0.2) !important;
        }
        /* Captions & footer */
        [data-testid="stCaptionContainer"] {
            color: #64748b !important;
        }
        </style>
        """,
        unsafe_allow_html=True,
    )


def polish_fig(fig: Any) -> Any:
    """Plotly layout tuned for dark Streamlit theme."""
    fig.update_layout(
        template="plotly_dark",
        font=dict(
            family="'Segoe UI', Inter, system-ui, sans-serif",
            size=13,
            color="#cbd5e1",
        ),
        title_font_size=15,
        title_font_color="#f1f5f9",
        title_x=0,
        margin=dict(l=8, r=8, t=52, b=8),
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(15, 23, 42, 0.55)",
        legend=dict(
            orientation="h",
            yanchor="bottom",
            y=1.02,
            xanchor="right",
            x=1,
            bgcolor="rgba(15, 23, 42, 0.75)",
            font=dict(color="#e2e8f0"),
        ),
        xaxis=dict(
            showgrid=True,
            gridcolor="rgba(148, 163, 184, 0.15)",
            zeroline=False,
            color="#94a3b8",
        ),
        yaxis=dict(
            showgrid=True,
            gridcolor="rgba(148, 163, 184, 0.15)",
            zeroline=False,
            color="#94a3b8",
        ),
    )
    return fig


def plotly_config() -> dict:
    return {
        "displayModeBar": True,
        "displaylogo": False,
        "modeBarButtonsToRemove": ["lasso2d", "select2d"],
        "toImageButtonOptions": {"format": "png", "scale": 2},
    }
