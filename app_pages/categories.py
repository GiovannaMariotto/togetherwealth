import streamlit as st

from functions.categories import CATEGORY_ICONS, DEFAULT_CATEGORIES
from functions.database import add_subcategory, read_subcategories
from utils.ui import category_select, render_header


def get_subcategory_map() -> dict:
    sub_df = read_subcategories()
    subcategory_map = {category: [] for category in DEFAULT_CATEGORIES.keys()}
    if not sub_df.empty:
        for category, group in sub_df.groupby("category"):
            custom_values = group["subcategory"].dropna().unique().tolist()
            subcategory_map.setdefault(category, [])
            subcategory_map[category] = sorted(set(custom_values))
    return subcategory_map


def render_categories() -> None:
    render_header()
    st.subheader("Categories and Custom Subcategories")
    subcategory_map = get_subcategory_map()
    for category, subcategories in subcategory_map.items():
        with st.expander(f"{CATEGORY_ICONS.get(category, '📌')} {category}"):
            if subcategories:
                st.write(", ".join(subcategories))
            else:
                st.caption("No subcategories yet.")

    st.divider()
    st.subheader("Add a Custom Subcategory")
    with st.form("subcategory_form", clear_on_submit=True):
        category = category_select("Category", "category_page_category")
        subcategory = st.text_input("New subcategory")
        submitted = st.form_submit_button("Add Subcategory")
    if submitted:
        add_subcategory(category, subcategory)
        st.success("Subcategory added.")
        st.rerun()