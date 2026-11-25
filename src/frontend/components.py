"""Frontend UI components and layout helpers for Streamlit."""

import streamlit as st


def apply_custom_styles() -> None:
    """Injects custom CSS styling for a modern university SaaS dashboard appearance."""
    st.markdown(
        """
        <style>
        /* Base typography & palette */
        .main-header {
            font-size: 2.2rem;
            font-weight: 700;
            color: #1E293B;
            margin-bottom: 0.2rem;
        }
        .sub-header {
            font-size: 1.05rem;
            color: #64748B;
            margin-bottom: 1.8rem;
        }
        /* Metrics Card */
        .metric-card {
            background: #FFFFFF;
            padding: 1.2rem;
            border-radius: 12px;
            border: 1px solid #E2E8F0;
            box-shadow: 0 1px 3px rgba(0,0,0,0.05);
            transition: all 0.2s ease;
        }
        .metric-card:hover {
            box-shadow: 0 4px 6px -1px rgba(0,0,0,0.1);
        }
        .metric-title {
            font-size: 0.85rem;
            text-transform: uppercase;
            letter-spacing: 0.05em;
            color: #64748B;
            font-weight: 600;
        }
        .metric-value {
            font-size: 1.8rem;
            font-weight: 700;
            color: #0F172A;
            margin-top: 0.2rem;
        }
        /* Status Badges */
        .badge-success {
            background-color: #ECFDF5;
            color: #047857;
            padding: 4px 10px;
            border-radius: 9999px;
            font-weight: 600;
            font-size: 0.8rem;
            display: inline-block;
        }
        </style>
        """,
        unsafe_allow_html=True,
    )


def render_metric_card(title: str, value: str, icon: str = "") -> None:
    """Renders a styled metric card."""
    st.markdown(
        f"""
        <div class="metric-card">
            <div class="metric-title">{icon} {title}</div>
            <div class="metric-value">{value}</div>
        </div>
        """,
        unsafe_allow_html=True,
    )
