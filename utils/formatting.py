def safe_float(value) -> float:
    if value in (None, ""):
        return 0.0
    try:
        if isinstance(value, str):
            value = value.replace(",", ".")
        return float(value)
    except (TypeError, ValueError):
        return 0.0


def currency(value: float) -> str:
    return f"€{safe_float(value):,.2f}"