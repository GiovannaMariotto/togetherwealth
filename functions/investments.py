ETF_PRESETS = [
    {"ETF Category": "Global Equity ETF", "Expected Return %": 6.0, "Risk Level": "Medium"},
    {"ETF Category": "S&P 500 ETF", "Expected Return %": 7.0, "Risk Level": "High"},
    {"ETF Category": "MSCI World ETF", "Expected Return %": 6.0, "Risk Level": "Medium"},
    {"ETF Category": "Emerging Markets ETF", "Expected Return %": 7.5, "Risk Level": "High"},
    {"ETF Category": "Euro Government Bond ETF", "Expected Return %": 2.5, "Risk Level": "Low"},
    {"ETF Category": "Money Market ETF", "Expected Return %": 2.0, "Risk Level": "Low"},
]


def weighted_expected_return(allocations):
    total_weight = sum(item["Allocation %"] for item in allocations)
    if total_weight == 0:
        return 0
    return sum((item["Allocation %"] / total_weight) * item["Expected Return %"] for item in allocations)
