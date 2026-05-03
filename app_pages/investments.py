import pandas as pd
import plotly.express as px
import streamlit as st

from functions.investments import ETF_PRESETS, weighted_expected_return
from utils.ui import render_header


def render_investments() -> None:
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
