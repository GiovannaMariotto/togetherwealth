import streamlit as st

from app_pages.add_values import render_add_values
from app_pages.categories import render_categories
from app_pages.dashboard import render_dashboard
from app_pages.excel_export import render_excel_export
from app_pages.investments import render_investments
from app_pages.projections import render_projections
from functions.analytics import prepare_summary
from functions.database import initialize_database, ensure_default_subcategories, read_transactions, save_partner_names
from utils.session import cached_euribor, load_partner_names
from utils.styles import apply_global_styles


PAGE_DASHBOARD = "Dashboard"
PAGE_ADD_VALUES = "Add Values"
PAGE_CATEGORIES = "Categories"
PAGE_INVESTMENTS = "Investments"
PAGE_PROJECTIONS = "Projections"
PAGE_EXCEL_EXPORT = "Excel Export"
PAGE_OPTIONS = [
    PAGE_DASHBOARD,
    PAGE_ADD_VALUES,
    PAGE_CATEGORIES,
    PAGE_INVESTMENTS,
    PAGE_PROJECTIONS,
    PAGE_EXCEL_EXPORT,
]


def configure_app() -> None:
    st.set_page_config(
        page_title="TogetherWealth",
        page_icon="💶",
        layout="wide",
        initial_sidebar_state="expanded",
    )
    apply_global_styles()
    initialize_database()
    ensure_default_subcategories()


def render_partner_sidebar() -> tuple[str, str]:
    partner_a, partner_b = load_partner_names()
    with st.sidebar.expander("Partner names", expanded=False):
        st.caption("Saved locally and reused every time you open the app.")
        new_partner_a = st.text_input("Partner 1 name", value=partner_a, placeholder="e.g., Giovanna")
        new_partner_b = st.text_input("Partner 2 name", value=partner_b, placeholder="e.g., Victor")
        if st.button("Save names"):
            save_partner_names(new_partner_a, new_partner_b)
            st.session_state.partner_a_name = new_partner_a.strip() or "Partner A"
            st.session_state.partner_b_name = new_partner_b.strip() or "Partner B"
            st.success("Partner names saved.")
            st.rerun()
    return st.session_state.partner_a_name, st.session_state.partner_b_name


def render_page(page: str, transactions, summary: dict, euribor: dict, partner_a: str, partner_b: str) -> None:
    if page == PAGE_DASHBOARD:
        render_dashboard(transactions, partner_a, partner_b)
    elif page == PAGE_ADD_VALUES:
        render_add_values()
    elif page == PAGE_CATEGORIES:
        render_categories()
    elif page == PAGE_INVESTMENTS:
        render_investments()
    elif page == PAGE_PROJECTIONS:
        render_projections(summary, euribor)
    elif page == PAGE_EXCEL_EXPORT:
        render_excel_export(transactions, summary, euribor, partner_a, partner_b)


def main() -> None:
    configure_app()
    partner_a, partner_b = render_partner_sidebar()
    page = st.sidebar.radio("Navigation", PAGE_OPTIONS)

    transactions = read_transactions()
    summary = prepare_summary(transactions)
    euribor = cached_euribor()
    render_page(page, transactions, summary, euribor, partner_a, partner_b)


if __name__ == "__main__":
    main()
    