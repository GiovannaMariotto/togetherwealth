def calculate_split(total_amount: float, method: str, income_a: float = 0, income_b: float = 0, custom_a_pct: float = 50):
    if method == "50/50":
        a_share = total_amount * 0.5
        b_share = total_amount * 0.5
    elif method == "Income-based":
        total_income = income_a + income_b
        if total_income <= 0:
            a_share = total_amount * 0.5
            b_share = total_amount * 0.5
        else:
            a_share = total_amount * (income_a / total_income)
            b_share = total_amount * (income_b / total_income)
    else:
        a_share = total_amount * (custom_a_pct / 100)
        b_share = total_amount - a_share
    return round(a_share, 2), round(b_share, 2)
