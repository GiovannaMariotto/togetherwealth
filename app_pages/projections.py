import plotly.express as px
import streamlit as st

from functions.projections import future_value_projection, scenario_rates
from models.projection import ProjectionInput
from utils.ui import render_header


def render_projections(summary: dict, euribor: dict) -> None:
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