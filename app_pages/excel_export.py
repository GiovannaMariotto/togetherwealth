import streamlit as st

from functions.export import build_excel_report
from functions.projections import future_value_projection, scenario_rates
from models.projection import ProjectionInput
from utils.ui import render_header


def render_excel_export(transactions, summary: dict, euribor: dict, partner_a_name: str, partner_b_name: str) -> None:
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
    dashboard_owners = ["All", "Shared", partner_a_name, partner_b_name]
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
        return

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