import pandas as pd
from models.projection import ProjectionInput


def future_value_projection(data: ProjectionInput) -> pd.DataFrame:
    monthly_return = data.annual_return_pct / 100 / 12
    rows = []
    balance = data.initial_amount

    for month_number in range(1, data.years * 12 + 1):
        balance = balance * (1 + monthly_return) + data.monthly_contribution
        if month_number % 12 == 0:
            year = month_number // 12
            rows.append(
                {
                    "Year": year,
                    "Projected Value": round(balance, 2),
                    "Monthly Contribution": data.monthly_contribution,
                    "Annual Return %": data.annual_return_pct,
                    "EURIBOR % Used": data.euribor_pct,
                }
            )
    return pd.DataFrame(rows)


def scenario_rates(euribor_pct: float) -> dict:
    return {
        "Conservative": max(euribor_pct, 0.0),
        "Realistic": max(euribor_pct + 3.0, 1.0),
        "Optimistic": max(euribor_pct + 5.5, 2.0),
    }
