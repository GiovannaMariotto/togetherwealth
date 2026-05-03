from datetime import date

import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st

from functions.analytics import filter_dashboard_transactions, prepare_cashflow_chart_data, prepare_summary
from functions.categories import CATEGORY_ICONS, DEFAULT_CATEGORIES
from functions.database import (
    add_subcategory,
    delete_transaction,
    ensure_default_subcategories,
    get_partner_names,
    get_subcategories,
    initialize_database,
    insert_transaction,
    read_subcategories,
    read_transactions,
    save_partner_names,
)
from functions.euribor_service import fetch_euribor_rate
from functions.export import build_excel_report
from functions.investments import ETF_PRESETS, weighted_expected_return
from functions.projections import future_value_projection, scenario_rates
from functions.splits import calculate_split
from models.projection import ProjectionInput
from models.transaction import Transaction, TransactionType

st.set_page_config(
    page_title="TogetherWealth",
    page_icon="💶",
    layout="wide",
    initial_sidebar_state="expanded",
)

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
st.markdown(CUSTOM_CSS, unsafe_allow_html=True)

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

initialize_database()
ensure_default_subcategories()


def currency(value: float) -> str:
    return f"€{safe_float(value):,.2f}"


def safe_float(value) -> float:
    if value in (None, ""):
        return 0.0
    try:
        if isinstance(value, str):
            value = value.replace(",", ".")
        return float(value)
    except (TypeError, ValueError):
        return 0.0


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
    category_labels = [f"{CATEGORY_ICONS.get(category, '')} {category}".strip() for category in category_values]
    if st.session_state.get(key) not in category_labels:
        st.session_state[key] = category_labels[0]
    selected_label = st.selectbox(label, category_labels, key=key)
    return selected_label.split(" ", 1)[1] if " " in selected_label else selected_label


def categories_for_transaction_type(transaction_type: str) -> list[str]:
    if transaction_type == TransactionType.income.value:
        return ["Income"]
    if transaction_type == TransactionType.saving.value:
        return ["Savings"]
    if transaction_type == TransactionType.investment.value:
        return ["Investments"]
    return NON_INCOME_CATEGORIES


def build_cashflow_figure(df: pd.DataFrame) -> go.Figure:
    """Build a clean cashflow waterfall chart.

    Plotly Waterfall does not support a generic `marker` argument.
    Colors must be defined through increasing/decreasing/totals.
    """
    if df.empty:
        fig = go.Figure()
        fig.update_layout(
            title="Cashflow",
            template="plotly_white",
            height=420,
        )
        return fig

    grouped = (
        df.groupby("type", as_index=False)["amount"]
        .sum()
        .sort_values("type")
    )

    income = float(grouped.loc[grouped["type"] == "Income", "amount"].sum())
    expenses = float(grouped.loc[grouped["type"] == "Expense", "amount"].sum())
    savings = float(grouped.loc[grouped["type"] == "Saving", "amount"].sum())
    investments = float(grouped.loc[grouped["type"] == "Investment", "amount"].sum())

    fig = go.Figure(
        go.Waterfall(
            name="Cashflow",
            orientation="v",
            measure=[
                "relative",
                "relative",
                "relative",
                "relative",
                "total",
            ],
            x=[
                "Income",
                "Expenses",
                "Savings",
                "Investments",
                "Net",
            ],
            y=[
                income,
                -expenses,
                -savings,
                -investments,
                0,
            ],
            text=[
                f"€{income:,.2f}",
                f"-€{expenses:,.2f}",
                f"-€{savings:,.2f}",
                f"-€{investments:,.2f}",
                "",
            ],
            textposition="outside",
            connector={"line": {"width": 1}},
            increasing={"marker": {"color": "#2E7D32"}},
            decreasing={"marker": {"color": "#C62828"}},
            totals={"marker": {"color": "#1565C0"}},
        )
    )

    fig.update_layout(
        title="Monthly Cashflow",
        template="plotly_white",
        height=420,
        showlegend=False,
        yaxis_title="Amount (€)",
    )

    return fig


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


def get_subcategory_map() -> dict:
    sub_df = read_subcategories()
    subcategory_map = {category: [] for category in DEFAULT_CATEGORIES.keys()}
    if not sub_df.empty:
        for category, group in sub_df.groupby("category"):
            custom_values = group["subcategory"].dropna().unique().tolist()
            subcategory_map.setdefault(category, [])
            subcategory_map[category] = sorted(set(custom_values))
    return subcategory_map


def subcategory_dropdown_with_custom(label: str, category: str, key_prefix: str) -> tuple[str, str]:
    options = [NO_SUBCATEGORY] + get_subcategories(category) + [ADD_NEW_SUBCATEGORY]
    select_key = f"{key_prefix}_select"
    new_key = f"{key_prefix}_new"
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


@st.cache_data(ttl=60 * 60)
def cached_euribor() -> dict:
    return fetch_euribor_rate()


def save_transaction(entry_date, partner, transaction_type, category, subcategory, source, amount, notes=None) -> None:
    amount_value = safe_float(amount)
    transaction = Transaction(
        entry_date=entry_date,
        month=entry_date.strftime("%Y-%m"),
        partner=partner,
        transaction_type=TransactionType(transaction_type),
        category=category,
        subcategory=subcategory or None,
        source=source or None,
        amount=amount_value,
        notes=notes or None,
    )
    insert_transaction(transaction)


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

page = st.sidebar.radio(
    "Navigation",
    ["Dashboard", "Add Values", "Categories", "Investments", "Projections", "Excel Export"],
)

transactions = read_transactions()
summary = prepare_summary(transactions)
euribor = cached_euribor()

if page == "Dashboard":
    render_header()
    st.markdown(
        f'<div class="info-card">Track {st.session_state.partner_a_name}, {st.session_state.partner_b_name}, and shared money in one place.</div>',
        unsafe_allow_html=True,
    )
    st.write("")

    if transactions.empty:
        st.info("No data yet. Go to Add Values to enter your first income, expense, saving, or investment.")
    else:
        months = sorted(transactions["month"].dropna().unique().tolist())
        owner_options = ["All", "Shared", st.session_state.partner_a_name, st.session_state.partner_b_name]
        segment_col, month_col = st.columns([1.35, 1.0])
        selected_owner = segment_col.radio(
            "Dashboard view",
            owner_options,
            horizontal=True,
            key="dashboard_owner_view",
        )
        selected_month = month_col.selectbox("View month", ["All months"] + months, index=len(months), key="dashboard_month")
        view_df = filter_dashboard_transactions(transactions, selected_month, selected_owner)
        view_summary = prepare_summary(view_df)
        chart_df, net_cashflow = prepare_cashflow_chart_data(view_df)

        st.write("")
        col1, col2, col3, col4 = st.columns(4)
        col1.metric("Income", currency(view_summary["income"]))
        col2.metric("Expenses", currency(view_summary["expenses"]))
        col3.metric("Saving / Overspend", currency(net_cashflow), delta_color="normal")
        col4.metric("Savings Rate", f"{view_summary['savings_rate']:.1f}%")

        if net_cashflow >= 0:
            st.success(f"This view is saving {currency(net_cashflow)} after expenses.")
        else:
            st.error(f"This view is over income by {currency(abs(net_cashflow))}.")

        st.divider()
        cashflow_col, breakdown_col = st.columns([1.35, 1.0])
        cashflow_col.plotly_chart(build_cashflow_figure(chart_df), use_container_width=True)

        expense_df = view_df[view_df["transaction_type"] == "Expense"]
        if not expense_df.empty:
            by_category = expense_df.groupby("category", as_index=False)["amount"].sum()
            fig = px.bar(
                by_category.sort_values("amount", ascending=True),
                x="amount",
                y="category",
                orientation="h",
                color="category",
                color_discrete_map=category_color_map(by_category["category"].tolist()),
                title="Expense Voices by Category",
                text_auto=".2s",
            )
            fig.update_layout(showlegend=False, xaxis_title="Amount (€)", yaxis_title=None, height=430)
            fig.update_xaxes(tickprefix="€")
            breakdown_col.plotly_chart(fig, use_container_width=True)
        else:
            breakdown_col.info("No expenses in this view yet.")

        monthly_base = transactions if selected_owner == "All" else transactions[transactions["partner"] == selected_owner]
        monthly = monthly_base.groupby(["month", "transaction_type"], as_index=False)["amount"].sum()
        fig3 = px.line(monthly, x="month", y="amount", color="transaction_type", markers=True, title="Historical Monthly Inputs")
        st.plotly_chart(fig3, use_container_width=True)

        st.subheader("Inputs in This View")
        st.dataframe(view_df, use_container_width=True, hide_index=True)

elif page == "Add Values":
    render_header()
    st.subheader("Add Values")
    st.caption("Each partner can add values independently at different times. Inputs are saved by month and shown together historically.")

    tab1, tab2, tab3 = st.tabs(["Add Voice", "Segment Total", "Quick Split"])

    with tab1:
        st.markdown("### Add one voice")
        st.caption("Fast entry for one income, expense, saving, or investment.")

        st.markdown('<div class="voice-panel"><div class="voice-title">Voice details</div>', unsafe_allow_html=True)
        col1, col2, col3, col4 = st.columns([1.0, 1.0, 1.0, 1.0])
        entry_date = col1.date_input("Date", value=date.today(), key="ind_date")
        transaction_type = col2.selectbox("Type", [item.value for item in TransactionType], key="ind_type")
        partner = col3.selectbox("Who is adding this?", partner_options(), key="ind_partner")
        amount = col4.number_input("Amount (€)", min_value=0.0, step=10.0, key="ind_amount")

        cat_col, sub_col = st.columns(2)
        with cat_col:
            category = category_select("Category", "ind_category", categories_for_transaction_type(transaction_type))
        with sub_col:
            subcategory, new_subcategory = subcategory_dropdown_with_custom("Subcategory", category, "ind_subcategory")
        source = st.text_input("Voice name / source", placeholder="e.g., Salary, Rent, Groceries, ETF contribution", key="ind_source")
        notes = st.text_area("Notes", placeholder="Optional", key="ind_notes")
        submitted = st.button("Save Voice", key="save_independent_voice", use_container_width=True)
        st.markdown("</div>", unsafe_allow_html=True)

        if submitted:
            if new_subcategory.strip():
                add_subcategory(category, new_subcategory.strip())
                subcategory = new_subcategory.strip()
            elif st.session_state.get("ind_subcategory_select") == ADD_NEW_SUBCATEGORY:
                st.warning("Write a new subcategory name before saving this entry.")
                st.stop()
            save_transaction(entry_date, partner, transaction_type, category, subcategory, source, amount, notes)
            st.success(f"Entry saved for {partner}.")
            st.rerun()

    with tab2:
        st.markdown("### Segment a first total into several voices")
        st.caption("Example: enter one salary amount first, then split it into rent, groceries, investments, bills, and savings.")
        if "segment_count" not in st.session_state:
            st.session_state.segment_count = 2

        col1, col2, col3 = st.columns(3)
        entry_date = col1.date_input("Date", value=date.today(), key="seg_date")
        partner = col2.selectbox("Owner", partner_options(), key="seg_partner")
        total_source = col3.text_input("First sum / source", value="Salary", key="seg_source")

        total_amount = st.number_input("First total amount (€)", min_value=0.0, step=50.0, key="seg_total")
        st.caption("Add each expense, saving, or investment voice. Leave a row at 0 if you are still deciding.")

        segment_rows = []
        for idx in range(st.session_state.segment_count):
            st.markdown(f'<div class="voice-panel"><div class="voice-title">Voice {idx + 1}</div>', unsafe_allow_html=True)
            c1, c2, c3, c4 = st.columns([1.0, 1.2, 1.2, 1.0])
            t_type = c1.selectbox("Type", SEGMENT_TRANSACTION_TYPES, key=f"seg_type_{idx}")
            with c2:
                cat = category_select("Category", f"seg_cat_{idx}", categories_for_transaction_type(t_type))
            with c3:
                sub, new_sub = subcategory_dropdown_with_custom("Subcategory", cat, f"seg_sub_{idx}")
            amt = c4.number_input("Amount (€)", min_value=0.0, step=10.0, key=f"seg_amt_{idx}")
            segment_rows.append((t_type, cat, sub, new_sub, safe_float(amt)))
            st.markdown("</div>", unsafe_allow_html=True)

        current_segment_total = sum(row[4] for row in segment_rows)
        current_remaining = safe_float(total_amount) - current_segment_total
        progress_value = 0.0 if safe_float(total_amount) == 0 else min(current_segment_total / safe_float(total_amount), 1.0)
        st.progress(progress_value)
        if current_remaining >= 0:
            st.markdown(f'<span class="status-green">Remaining to allocate: {currency(current_remaining)}</span>', unsafe_allow_html=True)
        else:
            st.markdown(f'<span class="status-red">Over the first total by {currency(abs(current_remaining))}</span>', unsafe_allow_html=True)

        action_col, notes_col = st.columns([0.35, 0.65])
        with action_col:
            if st.button("+ Add voice", key="add_segment_voice", use_container_width=True):
                st.session_state.segment_count += 1
                st.rerun()
            submitted_segments = st.button("Save Segmented Entries", key="save_segmented_entries", use_container_width=True)
        seg_notes = notes_col.text_area("Notes", placeholder="Optional", key="seg_notes")

        if submitted_segments:
            resolved_segments = []
            missing_subcategory = False
            for idx, (t_type, cat, sub, new_sub, amt) in enumerate(segment_rows):
                if new_sub.strip():
                    add_subcategory(cat, new_sub.strip())
                    sub = new_sub.strip()
                elif safe_float(amt) > 0 and st.session_state.get(f"seg_sub_{idx}_select") == ADD_NEW_SUBCATEGORY:
                    missing_subcategory = True
                resolved_segments.append((t_type, cat, sub, amt))

            positive_segments = [row for row in resolved_segments if safe_float(row[3]) > 0]
            total_amount_value = safe_float(total_amount)
            total_segments = sum(
                safe_float(row[3])
                for row in positive_segments
                if row[0] in SEGMENT_TRANSACTION_TYPES
            )
            if total_amount_value <= 0:
                st.error("Enter a first total amount greater than 0 before saving this segmented income.")
            elif missing_subcategory:
                st.warning("Write the new subcategory name for each row set to '+ Add new subcategory'.")
            elif total_segments > total_amount_value:
                over_limit = total_segments - total_amount_value
                st.markdown(
                    f"""
                    <div style="color:#b42318; font-weight:700;">
                        Segmented total: {currency(total_segments)}<br>
                        First total available: {currency(total_amount_value)}<br>
                        Over limit: {currency(over_limit)}
                    </div>
                    """,
                    unsafe_allow_html=True,
                )
                st.warning("The segmented total exceeds the available amount. Nothing was saved; adjust the voice amounts and try again.")
            else:
                income_subcategory = total_source.strip() or "Salary"
                add_subcategory("Income", income_subcategory)
                save_transaction(
                    entry_date,
                    partner,
                    TransactionType.income.value,
                    "Income",
                    income_subcategory,
                    total_source,
                    total_amount_value,
                    seg_notes,
                )
                for t_type, cat, sub, amt in positive_segments:
                    save_transaction(entry_date, partner, t_type, cat, sub, total_source, amt, seg_notes)
                remaining = total_amount_value - total_segments
                saved_count = len(positive_segments) + 1
                if remaining > 0:
                    add_subcategory("Savings", "Remaining from income")
                    save_transaction(
                        entry_date,
                        partner,
                        TransactionType.saving.value,
                        "Savings",
                        "Remaining from income",
                        f"Automatic saving from {total_source or 'income'}",
                        remaining,
                        seg_notes,
                    )
                    saved_count += 1
                st.success(f"Saved {saved_count} entries for {partner}: income, {len(positive_segments)} voice rows, and automatic saving of {currency(max(remaining, 0))}.")
                st.rerun()

    with tab3:
        st.markdown("### Quick split one total between partners")
        with st.form("quick_entry_form", clear_on_submit=False):
            col1, col2, col3 = st.columns(3)
            entry_date = col1.date_input("Date", value=date.today(), key="quick_date")
            transaction_type = col2.selectbox("Type", [item.value for item in TransactionType], key="quick_type")
            total_amount = col3.number_input("Total amount (€)", min_value=0.0, step=10.0, key="quick_total")

            split_method = st.selectbox("Split method", ["50/50", "Income-based", "Custom"], key="quick_split")
            income_a = income_b = 0.0
            custom_a_pct = 50.0
            if split_method == "Income-based":
                income_a = st.number_input(f"{st.session_state.partner_a_name} monthly income", min_value=0.0, step=100.0)
                income_b = st.number_input(f"{st.session_state.partner_b_name} monthly income", min_value=0.0, step=100.0)
            elif split_method == "Custom":
                custom_a_pct = st.slider(f"{st.session_state.partner_a_name} %", min_value=0, max_value=100, value=50)

            quick_cat_col, quick_sub_col = st.columns(2)
            with quick_cat_col:
                category = category_select("Category", "quick_cat", categories_for_transaction_type(transaction_type))
            with quick_sub_col:
                subcategory, new_subcategory = subcategory_dropdown_with_custom("Subcategory", category, "quick_subcategory")
            source = st.text_input("Source / voice", placeholder="e.g., Salary, N26, ETF contribution", key="quick_source")
            submitted_quick = st.form_submit_button("Save Split Entries")

        if submitted_quick:
            if new_subcategory.strip():
                add_subcategory(category, new_subcategory.strip())
                subcategory = new_subcategory.strip()
            elif st.session_state.get("quick_subcategory_select") == ADD_NEW_SUBCATEGORY:
                st.warning("Write a new subcategory name before saving these split entries.")
                st.stop()
            a_share, b_share = calculate_split(safe_float(total_amount), split_method, safe_float(income_a), safe_float(income_b), safe_float(custom_a_pct))
            for partner_value, amount_value in [(st.session_state.partner_a_name, a_share), (st.session_state.partner_b_name, b_share)]:
                save_transaction(entry_date, partner_value, transaction_type, category, subcategory, source, amount_value)
            st.success(f"Saved split entries: {st.session_state.partner_a_name} {currency(a_share)}, {st.session_state.partner_b_name} {currency(b_share)}.")
            st.rerun()

    st.divider()
    st.subheader("Same Month and Historical Inputs")
    updated_df = read_transactions()
    if updated_df.empty:
        st.info("No entries yet.")
    else:
        months = sorted(updated_df["month"].dropna().unique().tolist())
        selected_month = st.selectbox("Filter table by month", ["All months"] + months, index=len(months), key="entry_month_filter")
        table_df = updated_df if selected_month == "All months" else updated_df[updated_df["month"] == selected_month]
        st.dataframe(table_df, use_container_width=True, hide_index=True)
        delete_id = st.number_input("Transaction ID to delete", min_value=0, step=1)
        if st.button("Delete selected transaction") and delete_id > 0:
            delete_transaction(int(delete_id))
            st.success("Transaction deleted.")
            st.rerun()

elif page == "Categories":
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

elif page == "Investments":
    render_header()
    st.subheader("ETF Educational Planner")
    st.warning("Educational only, not financial advice.")

    allocations = []
    cols = st.columns(2)
    for idx, preset in enumerate(ETF_PRESETS):
        with cols[idx % 2]:
            st.markdown(f"**{preset['ETF Category']}** — Risk: {preset['Risk Level']}")
            allocation = st.slider(f"Allocation % - {preset['ETF Category']}", 0, 100, 0, key=f"alloc_{idx}")
            expected_return = st.number_input(
                f"Expected return % - {preset['ETF Category']}",
                value=float(preset["Expected Return %"]),
                step=0.5,
                key=f"ret_{idx}",
            )
            allocations.append(
                {
                    "ETF Category": preset["ETF Category"],
                    "Allocation %": allocation,
                    "Expected Return %": expected_return,
                    "Risk Level": preset["Risk Level"],
                }
            )

    allocation_df = pd.DataFrame(allocations)
    total_allocation = allocation_df["Allocation %"].sum()
    st.metric("Total Allocation", f"{total_allocation:.0f}%")
    if total_allocation != 100:
        st.info("For a full portfolio simulation, total allocation should equal 100%.")

    if total_allocation > 0:
        weighted_return = weighted_expected_return(allocations)
        st.metric("Weighted Expected Return", f"{weighted_return:.2f}%")
        fig = px.pie(allocation_df[allocation_df["Allocation %"] > 0], values="Allocation %", names="ETF Category", title="ETF Allocation")
        st.plotly_chart(fig, use_container_width=True)

elif page == "Projections":
    render_header()
    st.subheader("EURIBOR-Based Projections")
    st.caption(f"EURIBOR reference: {euribor['rate']:.2f}% | Source: {euribor['source']} | Date: {euribor['date']}")

    col1, col2, col3 = st.columns(3)
    initial_amount = col1.number_input("Initial amount (€)", min_value=0.0, value=float(summary["savings"] + summary["investments"]), step=100.0)
    monthly_contribution = col2.number_input("Monthly contribution (€)", min_value=0.0, value=500.0, step=50.0)
    years = col3.slider("Years", min_value=1, max_value=30, value=10)

    scenarios = scenario_rates(euribor["rate"])
    scenario = st.selectbox("Scenario", list(scenarios.keys()))
    annual_return = st.number_input("Annual return %", value=float(scenarios[scenario]), step=0.25)

    projection_input = ProjectionInput(
        initial_amount=initial_amount,
        monthly_contribution=monthly_contribution,
        annual_return_pct=annual_return,
        years=years,
        euribor_pct=euribor["rate"],
    )
    projection_df = future_value_projection(projection_input)
    fig = px.line(projection_df, x="Year", y="Projected Value", markers=True, title="Projected Wealth Over Time")
    st.plotly_chart(fig, use_container_width=True)
    st.dataframe(projection_df, use_container_width=True, hide_index=True)

elif page == "Excel Export":
    render_header()
    st.subheader("Download Excel Report")
    st.write("Export a clean Excel workbook with dashboards for all money, shared money, and each partner.")

    default_projection = future_value_projection(
        ProjectionInput(
            initial_amount=float(summary["savings"] + summary["investments"]),
            monthly_contribution=500,
            annual_return_pct=scenario_rates(euribor["rate"])["Realistic"],
            years=10,
            euribor_pct=euribor["rate"],
        )
    )
    dashboard_owners = ["All", "Shared", st.session_state.partner_a_name, st.session_state.partner_b_name]
    excel_bytes = build_excel_report(transactions, default_projection, dashboard_owners=dashboard_owners)
    st.download_button(
        label="Download Excel Report",
        data=excel_bytes,
        file_name="togetherwealth_report.xlsx",
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
    )

    st.subheader("Preview")
    if transactions.empty:
        st.info("No transactions yet. The exported file will contain empty tables and a basic dashboard.")
    else:
        preview_tabs = st.tabs(["All Inputs", "Income", "Expenses", "Savings", "Investments"])
        typed_frames = {
            "All Inputs": transactions,
            "Income": transactions[transactions["transaction_type"] == "Income"],
            "Expenses": transactions[transactions["transaction_type"] == "Expense"],
            "Savings": transactions[transactions["transaction_type"] == "Saving"],
            "Investments": transactions[transactions["transaction_type"] == "Investment"],
        }
        for tab, (label, frame) in zip(preview_tabs, typed_frames.items()):
            with tab:
                if frame.empty:
                    st.info(f"No {label.lower()} yet.")
                else:
                    st.dataframe(frame, use_container_width=True, hide_index=True)