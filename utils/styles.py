import streamlit as st


CUSTOM_CSS = """
<style>
    .block-container {padding-top: 1.25rem; padding-bottom: 2rem; max-width: 1180px;}
    h1, h2, h3 {letter-spacing: 0;}
    div[data-testid="stMetric"] {
        background: #ffffff;
        border: 1px solid #e8edf3;
        padding: 0.9rem;
        border-radius: 8px;
        box-shadow: 0 4px 14px rgba(31, 41, 55, 0.04);
    }
    .info-card {
        background: #f8fbff;
        border: 1px solid #e8edf3;
        border-radius: 8px;
        padding: 1rem;
        box-shadow: 0 4px 14px rgba(31, 41, 55, 0.04);
    }
    .voice-panel {
        background: #ffffff;
        border: 1px solid #e8edf3;
        border-radius: 8px;
        padding: 1rem;
        margin: 0.55rem 0;
        box-shadow: 0 4px 14px rgba(31, 41, 55, 0.04);
    }
    .voice-title {
        color: #111827;
        font-size: 0.96rem;
        font-weight: 700;
        margin-bottom: 0.35rem;
    }
    .status-green {
        color: #16803c;
        font-weight: 800;
    }
    .status-red {
        color: #b42318;
        font-weight: 800;
    }
    .small-muted {color: #6b7280; font-size: 0.92rem;}
</style>
"""


def apply_global_styles() -> None:
    st.markdown(CUSTOM_CSS, unsafe_allow_html=True)
