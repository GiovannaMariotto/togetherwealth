import pandas as pd
import plotly.graph_objects as go

from utils.formatting import currency
from utils.ui import category_color_map


def build_cashflow_figure(chart_df: pd.DataFrame) -> go.Figure:
    fig = go.Figure()
    if chart_df.empty:
        fig.update_layout(title="Income, Expenses, and Net")
        return fig

    final_group = chart_df["color_group"].iloc[-1]
    total_color = "#16803C" if final_group == "Saved" else "#B42318"
    text_values = [currency(value) for value in chart_df["display_amount"]]
    fig.add_trace(
        go.Waterfall(
            x=chart_df["voice"],
            y=chart_df["amount"],
            measure=chart_df["measure"],
            text=text_values,
            textposition="outside",
            connector={"line": {"color": "#D9E1EC", "width": 1}},
            increasing={"marker": {"color": "#5DADEC"}},
            decreasing={"marker": {"color": "#F97066"}},
            totals={"marker": {"color": total_color}},
            hovertemplate="%{x}<br>%{text}<extra></extra>",
        )
    )

    fig.update_layout(
        title="Staggered Expenses",
        yaxis_title="Amount (€)",
        xaxis_title=None,
        showlegend=False,
        height=430,
        margin=dict(l=20, r=20, t=60, b=30),
    )
    fig.update_yaxes(tickprefix="€")
    return fig