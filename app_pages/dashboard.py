import plotly.express as px
import streamlit as st

from functions.analytics import filter_dashboard_transactions, prepare_cashflow_chart_data, prepare_summary, to_numeric_amounts
from utils.charts import build_cashflow_figure
from utils.formatting import currency
from utils.ui import category_color_map, render_header

def _expense_subcategory_breakdown(expense_df, monthly_income: float = 0.0):
    if expense_df.empty:
        return expense_df
    breakdown = to_numeric_amounts(expense_df)
    breakdown["subcategory"] = breakdown["subcategory"].fillna("No subcategory").replace("", "No subcategory")
    breakdown = breakdown.groupby(["category", "subcategory"], as_index=False)["amount"].sum()
    totals = breakdown.groupby("category")["amount"].transform("sum")
    breakdown["category_share"] = (breakdown["amount"] / totals * 100).fillna(0.0)
    breakdown["income_share"] = 0.0
    if monthly_income > 0:
        breakdown["income_share"] = (breakdown["amount"] / monthly_income * 100).fillna(0.0)
    return breakdown.sort_values(["category", "amount"], ascending=[True, False])


def _render_subcategory_section(expense_df, monthly_income: float) -> None:
    st.subheader("Category Details")
    if expense_df.empty:
        st.info("No expenses to break down by subcategory in this view.")
        return

    sub_breakdown = _expense_subcategory_breakdown(expense_df, monthly_income)
    tree_col, table_col = st.columns([1.15, 1.0])
    fig = px.treemap(
        sub_breakdown,
        path=["category", "subcategory"],
        values="amount",
        color="category",
        color_discrete_map=category_color_map(sub_breakdown["category"].unique().tolist()),
        title="Category and Subcategory Map",
    )
    fig.update_traces(texttemplate="%{label}<br>€%{value:,.0f}")
    fig.update_layout(margin=dict(l=10, r=10, t=45, b=10), height=420)
    tree_col.plotly_chart(fig, use_container_width=True)

    display_df = sub_breakdown.copy()
    display_df["amount"] = display_df["amount"].map(currency)
    display_df["category_share"] = display_df["category_share"].map(lambda value: f"{value:.1f}%")
    display_df["income_share"] = display_df["income_share"].map(lambda value: f"{value:.1f}%")
    table_col.dataframe(
        display_df.rename(columns={"category": "Category", "subcategory": "Subcategory", "amount": "Amount", "category_share": "Share in category"}),
        display_df.rename(
            columns={
                "category": "Category",
                "subcategory": "Subcategory",
                "amount": "Amount",
                "category_share": "Share in category",
                "income_share": "Share of monthly income",
            }
        ),
        use_container_width=True,
        hide_index=True,
    )


def _render_exploration_views(view_df, transactions, selected_owner: str) -> None:
    st.subheader("Explore Further")
    if view_df.empty:
        st.info("No data to explore in this view yet.")
        return

    monthly_base = transactions if selected_owner == "All" else transactions[transactions["partner"] == selected_owner]
    monthly_base = to_numeric_amounts(monthly_base)
    tab1, tab2, tab3 = st.tabs(["Monthly Rhythm", "Top Voices", "Money Mix"])

    with tab1:
        monthly_expenses = monthly_base[monthly_base["transaction_type"] == "Expense"]
        if monthly_expenses.empty:
            st.info("No expenses yet for the monthly rhythm view.")
        else:
            heatmap_df = monthly_expenses.groupby(["category", "month"], as_index=False)["amount"].sum()
            fig = px.density_heatmap(
                heatmap_df,
                x="month",
                y="category",
                z="amount",
                color_continuous_scale="Blues",
                title="Monthly Expense Rhythm",
                text_auto=".2s",
            )
            fig.update_layout(height=420, xaxis_title=None, yaxis_title=None)
            st.plotly_chart(fig, use_container_width=True)

    with tab2:
        voice_df = view_df.copy()
        voice_df["subcategory"] = voice_df["subcategory"].fillna("No subcategory").replace("", "No subcategory")
        voice_df["source"] = voice_df["source"].fillna("No source").replace("", "No source")
        voice_df["voice"] = voice_df.apply(
            lambda row: row["source"] if row["source"] != "No source" else row["subcategory"],
            axis=1,
        )
        top_voices = voice_df.groupby(["transaction_type", "category", "voice"], as_index=False)["amount"].sum()
        top_voices = top_voices.sort_values("amount", ascending=False).head(12)
        if top_voices.empty:
            st.info("No voices to rank yet.")
        else:
            fig = px.bar(
                top_voices.sort_values("amount"),
                x="amount",
                y="voice",
                color="transaction_type",
                orientation="h",
                title="Top Voices in This View",
                hover_data=["category"],
                text_auto=".2s",
            )
            fig.update_layout(height=430, xaxis_title="Amount (€)", yaxis_title=None)
            fig.update_xaxes(tickprefix="€")
            st.plotly_chart(fig, use_container_width=True)

    with tab3:
        mix_df = view_df.groupby("transaction_type", as_index=False)["amount"].sum()
        if mix_df.empty:
            st.info("No money mix to show yet.")
        else:
            fig = px.pie(
                mix_df,
                names="transaction_type",
                values="amount",
                hole=0.55,
                title="Money Mix by Type",
                color="transaction_type",
                color_discrete_map={
                    "Income": "#5DADEC",
                    "Expense": "#F97066",
                    "Saving": "#16803C",
                    "Investment": "#7C3AED",
                },
            )
            fig.update_traces(textposition="inside", textinfo="percent+label")
            fig.update_layout(height=420)
            st.plotly_chart(fig, use_container_width=True)

def render_dashboard(transactions, partner_a_name: str, partner_b_name: str) -> None:
    render_header()
    st.markdown(
        f'<div class="info-card">Track {partner_a_name}, {partner_b_name}, and shared money in one place.</div>',
        unsafe_allow_html=True,
    )
    st.write("")

    if transactions.empty:
        st.info("No data yet. Go to Add Values to enter your first income, expense, saving, or investment.")
        return

    months = sorted(transactions["month"].dropna().unique().tolist())
    owner_options = ["All", "Shared", partner_a_name, partner_b_name]
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

    st.divider()
    _render_subcategory_section(expense_df, view_summary["income"])

    st.divider()
    _render_exploration_views(view_df, transactions, selected_owner)

    st.divider()

    monthly_base = transactions if selected_owner == "All" else transactions[transactions["partner"] == selected_owner]
    monthly = monthly_base.groupby(["month", "transaction_type"], as_index=False)["amount"].sum()
    fig3 = px.line(monthly, x="month", y="amount", color="transaction_type", markers=True, title="Historical Monthly Inputs")
    st.plotly_chart(fig3, use_container_width=True)

    st.subheader("Inputs in This View")
    st.dataframe(view_df, use_container_width=True, hide_index=True)