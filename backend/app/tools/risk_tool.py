def risk_tool(
    technical_data: dict
):

    volatility = technical_data[
        "volatility"
    ]

    current_support = technical_data[
        "support"
    ]

    current_resistance = technical_data[
        "resistance"
    ]

    risks = []

    if volatility > 30:
        risks.append(
            "High volatility risk"
        )

    if technical_data["rsi"] > 75:
        risks.append(
            "Overbought condition"
        )

    if technical_data["rsi"] < 25:
        risks.append(
            "Oversold condition"
        )

    return {
        "worst_case_estimate":
            current_support,

        "best_case_estimate":
            current_resistance,

        "key_risks": risks
    }