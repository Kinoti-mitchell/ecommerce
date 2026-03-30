"""Shared UI helpers: CSS and Plotly polish for Streamlit."""

from __future__ import annotations

from typing import Any

# Consistent categorical colors (accessible, print-friendly)
FRAUD_COLORS = {"0": "#0d9488", "1": "#e11d48"}  # teal / rose
SENTIMENT_COLORS = {
    "positive": "#059669",
    "negative": "#dc2626",
    "neutral": "#64748b",
}


def inject_custom_css() -> None:
    import streamlit as st

    st.markdown(
        """
        <style>
        /* Page breathing room */
        .block-container {
            padding-top: 1.25rem;
            padding-bottom: 2.5rem;
            max-width: 1200px;
        }
        /* Title */
        h1 {
            font-weight: 700 !important;
            letter-spacing: -0.02em;
            color: #0f172a !important;
        }
        /* Expanders: card-like */
        div[data-testid="stExpander"] details {
            border: 1px solid #e2e8f0;
            border-radius: 12px;
            padding: 0.35rem 0.65rem;
            background: linear-gradient(180deg, #f8fafc 0%, #ffffff 100%);
        }
        /* Tab labels slightly bolder */
        button[data-baseweb="tab"] {
            font-weight: 600 !important;
        }
        /* Metric strip */
        div[data-testid="metric-container"] {
            background: #f1f5f9;
            border: 1px solid #e2e8f0;
            border-radius: 10px;
            padding: 0.65rem 0.85rem;
        }
        </style>
        """,
        unsafe_allow_html=True,
    )


def polish_fig(fig: Any) -> Any:
    """Apply consistent typography and margins to a Plotly figure."""
    fig.update_layout(
        template="plotly_white",
        font=dict(
            family="Inter, 'Segoe UI', system-ui, sans-serif",
            size=13,
            color="#334155",
        ),
        title_font_size=15,
        title_x=0,
        margin=dict(l=8, r=8, t=48, b=8),
        paper_bgcolor="rgba(255,255,255,0)",
        plot_bgcolor="#fafafa",
        legend=dict(
            orientation="h",
            yanchor="bottom",
            y=1.02,
            xanchor="right",
            x=1,
            bgcolor="rgba(255,255,255,0.8)",
        ),
        xaxis=dict(showgrid=True, gridcolor="#e2e8f0", zeroline=False),
        yaxis=dict(showgrid=True, gridcolor="#e2e8f0", zeroline=False),
    )
    return fig


def plotly_config() -> dict:
    """Fewer chart chrome distractions; keep download."""
    return {
        "displayModeBar": True,
        "displaylogo": False,
        "modeBarButtonsToRemove": ["lasso2d", "select2d"],
        "toImageButtonOptions": {"format": "png", "scale": 2},
    }
