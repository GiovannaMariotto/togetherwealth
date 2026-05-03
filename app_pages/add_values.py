from datetime import date

import streamlit as st

from functions.database import add_subcategory, delete_transaction, read_transactions
from functions.splits import calculate_split
from models.transaction import TransactionType
from utils.formatting import currency, safe_float
from utils.session import partner_options
from utils.transactions import save_transaction
from utils.ui import (
    ADD_NEW_SUBCATEGORY,
    SEGMENT_TRANSACTION_TYPES,
    categories_for_transaction_type,
    category_select,
    render_header,
    subcategory_dropdown_with_custom,
)


def render_add_values() -> None:
    render_header()
    st.subheader("Add Values")
    st.caption("Each partner can add values independently at different times. Inputs are saved by month and shown together historically.")

    tab1, tab2, tab3 = st.tabs(["Add Voice", "Segment Total", "Quick Split"])

    with tab1:
        _render_add_voice_tab()
    with tab2:
        _render_segment_total_tab()
    with tab3:
        _render_quick_split_tab()

    _render_recent_inputs()


def _render_add_voice_tab() -> None:
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


def _render_segment_total_tab() -> None:
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
        _save_segmented_entries(segment_rows, entry_date, partner, total_source, total_amount, seg_notes)


def _save_segmented_entries(segment_rows, entry_date, partner, total_source, total_amount, seg_notes) -> None:
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
    total_segments = sum(safe_float(row[3]) for row in positive_segments if row[0] in SEGMENT_TRANSACTION_TYPES)
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
        save_transaction(entry_date, partner, TransactionType.income.value, "Income", income_subcategory, total_source, total_amount_value, seg_notes)
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


def _render_quick_split_tab() -> None:
    st.markdown("### Quick split one total between partners")

    # These stay outside the form so category/subcategory refresh immediately.
    col1, col2 = st.columns(2)

    transaction_type = col1.selectbox(
        "Type",
        [item.value for item in TransactionType],
        key="quick_type",
    )

    category = col2.selectbox(
        "Category",
        categories_for_transaction_type(transaction_type),
        key="quick_cat",
    )

    subcategory, new_subcategory = subcategory_dropdown_with_custom(
        "Subcategory",
        category,
        "quick_subcategory",
    )

    with st.form("quick_entry_form", clear_on_submit=False):
        col1, col2 = st.columns(2)
        entry_date = col1.date_input("Date", value=date.today(), key="quick_date")
        total_amount = col2.number_input(
            "Total amount (€)",
            min_value=0.0,
            step=10.0,
            key="quick_total",
        )

        split_method = st.selectbox(
            "Split method",
            ["50/50", "Income-based", "Custom"],
            key="quick_split",
        )

        income_a = income_b = 0.0
        custom_a_pct = 50.0

        if split_method == "Income-based":
            income_a = st.number_input(
                f"{st.session_state.partner_a_name} monthly income",
                min_value=0.0,
                step=100.0,
                key="quick_income_a",
            )
            income_b = st.number_input(
                f"{st.session_state.partner_b_name} monthly income",
                min_value=0.0,
                step=100.0,
                key="quick_income_b",
            )

        elif split_method == "Custom":
            custom_a_pct = st.slider(
                f"{st.session_state.partner_a_name} %",
                min_value=0,
                max_value=100,
                value=50,
                key="quick_custom_a_pct",
            )

        source = st.text_input(
            "Source / voice",
            placeholder="e.g., Salary, N26, ETF contribution",
            key="quick_source",
        )

        submitted_quick = st.form_submit_button("Save Split Entries")

    if submitted_quick:
        if new_subcategory.strip():
            add_subcategory(category, new_subcategory.strip())
            subcategory = new_subcategory.strip()

        elif st.session_state.get("quick_subcategory_select") == ADD_NEW_SUBCATEGORY:
            st.warning("Write a new subcategory name before saving these split entries.")
            st.stop()

        a_share, b_share = calculate_split(
            safe_float(total_amount),
            split_method,
            safe_float(income_a),
            safe_float(income_b),
            safe_float(custom_a_pct),
        )

        for partner_value, amount_value in [
            (st.session_state.partner_a_name, a_share),
            (st.session_state.partner_b_name, b_share),
        ]:
            save_transaction(
                entry_date,
                partner_value,
                transaction_type,
                category,
                subcategory,
                source,
                amount_value,
            )

        st.success(
            f"Saved split entries: "
            f"{st.session_state.partner_a_name} {currency(a_share)}, "
            f"{st.session_state.partner_b_name} {currency(b_share)}."
        )
        st.rerun()

def _render_recent_inputs() -> None:
    st.divider()
    st.subheader("Same Month and Historical Inputs")
    updated_df = read_transactions()
    if updated_df.empty:
        st.info("No entries yet.")
        return

    months = sorted(updated_df["month"].dropna().unique().tolist())
    selected_month = st.selectbox("Filter table by month", ["All months"] + months, index=len(months), key="entry_month_filter")
    table_df = updated_df if selected_month == "All months" else updated_df[updated_df["month"] == selected_month]
    st.dataframe(table_df, use_container_width=True, hide_index=True)
    delete_id = st.number_input("Transaction ID to delete", min_value=0, step=1)
    if st.button("Delete selected transaction") and delete_id > 0:
        delete_transaction(int(delete_id))
        st.success("Transaction deleted.")
        st.rerun()