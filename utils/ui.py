from __future__ import annotations
import plotly.express as px
import streamlit as st

import plotly.express as px
from functions.categories import CATEGORY_ICONS, DEFAULT_CATEGORIES
from functions.database import get_subcategories
from models.transaction import TransactionType

ADD_NEW_SUBCATEGORY = "+ Add new subcategory"
NO_SUBCATEGORY = "No subcategory"
SEGMENT_TRANSACTION_TYPES = [
    TransactionType.expense.value,
    TransactionType.saving.value,
    TransactionType.investment.value,
]
NON_INCOME_CATEGORIES = [
    category for category in DEFAULT_CATEGORIES.keys() if category != "Income"
]
CATEGORY_PALETTE = px.colors.qualitative.Safe + px.colors.qualitative.Pastel
SPECIAL_BAR_COLORS = {
    "Income": "#5DADEC",
    "Saved": "#16803C",
    "Over budget": "#B42318",
}

NON_TRANSACTION_CATEGORIES = {
    "Income",
    "Savings",
    "Investments",
}

EXPENSE_CATEGORIES = [
    category for category in DEFAULT_CATEGORIES.keys()
    if category not in NON_TRANSACTION_CATEGORIES
]


def render_header() -> None:
    st.title("TogetherWealth 💶")
    st.caption("A clean MVP for couples to track shared finances, investments, and long-term projections.")


def category_color_map(categories: list[str]) -> dict[str, str]:
    color_map = dict(SPECIAL_BAR_COLORS)
    for idx, category in enumerate(categories):
        if category in color_map:
            continue
        color_map[category] = CATEGORY_PALETTE[idx % len(CATEGORY_PALETTE)]
    return color_map


def category_select(label: str, key: str, categories: list[str] | None = None) -> str:
    category_values = categories or list(DEFAULT_CATEGORIES.keys())
    if st.session_state.get(key) not in category_values:
        st.session_state[key] = category_values[0]
    return st.selectbox(
        label,
        category_values,
        key=key,
        format_func=lambda category: f"{CATEGORY_ICONS.get(category, '')} {category}".strip(),
    )

def categories_for_transaction_type(transaction_type: str) -> list[str]:
    if transaction_type == TransactionType.income.value:
        return ["Income"]
    if transaction_type == TransactionType.saving.value:
        return ["Savings"]
    if transaction_type == TransactionType.investment.value:
        return ["Investments"]
    if transaction_type == TransactionType.expense.value:
        return EXPENSE_CATEGORIES
    return list(DEFAULT_CATEGORIES.keys())

def subcategory_dropdown_with_custom(label: str, category: str, key_prefix: str) -> tuple[str, str]:
    options = [NO_SUBCATEGORY] + get_subcategories(category) + [ADD_NEW_SUBCATEGORY]

    select_key = f"{key_prefix}_select"
    new_key = f"{key_prefix}_new"
    category_key = f"{key_prefix}_category"

    if st.session_state.get(category_key) != category:
        st.session_state[category_key] = category
        st.session_state[select_key] = NO_SUBCATEGORY
        st.session_state[new_key] = ""

    if st.session_state.get(select_key) not in options:
        st.session_state[select_key] = NO_SUBCATEGORY

    selected = st.selectbox(
        label,
        options,
        key=select_key,
        help=f"Only subcategories saved under {category} are shown here.",
    )

    if selected == ADD_NEW_SUBCATEGORY:
        new_subcategory = st.text_input(
            "New subcategory",
            key=new_key,
            placeholder=f"Add a {category.lower()} subcategory",
        )
        return "", new_subcategory

    if selected == NO_SUBCATEGORY:
        return "", ""

    return selected, ""