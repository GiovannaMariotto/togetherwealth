import pandas as pd
from functions.categories import CATEGORY_GROUPS


def to_numeric_amounts(df: pd.DataFrame) -> pd.DataFrame:
    if df.empty:
        return df
    df = df.copy()
    df["amount"] = pd.to_numeric(df["amount"], errors="coerce").fillna(0.0)
    return df


def prepare_summary(df: pd.DataFrame) -> dict:
    if df.empty:
        return {
            "income": 0,
            "expenses": 0,
            "savings": 0,
            "investments": 0,
            "net_worth_proxy": 0,
            "savings_rate": 0,
        }
    df = to_numeric_amounts(df)
    income = df.loc[df["transaction_type"] == "Income", "amount"].sum()
    expenses = df.loc[df["transaction_type"] == "Expense", "amount"].sum()
    savings = df.loc[df["transaction_type"] == "Saving", "amount"].sum()
    investments = df.loc[df["transaction_type"] == "Investment", "amount"].sum()
    savings_rate = ((savings + investments) / income * 100) if income > 0 else 0
    return {
        "income": income,
        "expenses": expenses,
        "savings": savings,
        "investments": investments,
        "net_worth_proxy": savings + investments,
        "savings_rate": savings_rate,
    }


def add_group_column(df: pd.DataFrame) -> pd.DataFrame:
    if df.empty:
        return df
    df = df.copy()
    df["group"] = df["category"].map(CATEGORY_GROUPS).fillna("Variable")
    return df


def filter_dashboard_transactions(df: pd.DataFrame, month: str, owner: str) -> pd.DataFrame:
    if df.empty:
        return df

    filtered = to_numeric_amounts(df)
    if month != "All months":
        filtered = filtered[filtered["month"] == month]
    if owner != "All":
        filtered = filtered[filtered["partner"] == owner]
    return filtered


def prepare_cashflow_chart_data(df: pd.DataFrame) -> tuple[pd.DataFrame, float]:
    if df.empty:
        return pd.DataFrame(columns=["voice", "amount", "measure", "color_group", "display_amount"]), 0.0

    df = to_numeric_amounts(df)
    income = df.loc[df["transaction_type"] == "Income", "amount"].sum()
    expense_df = df[df["transaction_type"] == "Expense"]
    by_category = expense_df.groupby("category", as_index=False)["amount"].sum().sort_values("amount", ascending=False)

    rows = []
    if income > 0:
        rows.append(
            {
                "voice": "Income",
                "amount": income,
                "measure": "relative",
                "color_group": "Income",
                "display_amount": income,
            }
        )

    for row in by_category.itertuples(index=False):
        rows.append(
            {
                "voice": row.category,
                "amount": -row.amount,
                "measure": "relative",
                "color_group": row.category,
                "display_amount": row.amount,
            }
        )

    net = income - by_category["amount"].sum()
    rows.append(
        {
            "voice": "Saved" if net >= 0 else "Over budget",
            "amount": net,
            "measure": "total",
            "color_group": "Saved" if net >= 0 else "Over budget",
            "display_amount": abs(net),
        }
    )
    return pd.DataFrame(rows), net
