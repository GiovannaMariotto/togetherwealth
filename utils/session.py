import streamlit as st

from functions.database import get_partner_names
from functions.euribor_service import fetch_euribor_rate


def load_partner_names() -> tuple[str, str]:
    if "partner_a_name" not in st.session_state or "partner_b_name" not in st.session_state:
        partner_a, partner_b = get_partner_names()
        st.session_state.partner_a_name = partner_a
        st.session_state.partner_b_name = partner_b
    return st.session_state.partner_a_name, st.session_state.partner_b_name


def partner_options(include_shared: bool = True) -> list[str]:
    partner_a, partner_b = load_partner_names()
    options = [partner_a, partner_b]
    if include_shared:
        options.append("Shared")
    return options


@st.cache_data(ttl=60 * 60)
def cached_euribor() -> dict:
    return fetch_euribor_rate()
