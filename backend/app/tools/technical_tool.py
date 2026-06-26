from services.indicators import (
    calculate_sma,
    calculate_ema,
    calculate_rsi,
    calculate_macd,
    calculate_bollinger_bands,
    calculate_atr,
    calculate_volatility,
    calculate_drawdown
)

from utils.json_safe import safe_float

import math


def clean_number(value):

    if value is None:
        return None

    try:
        value = float(value)

        if math.isnan(value):
            return None

        if math.isinf(value):
            return None

        return round(value, 2)

    except Exception:
        return None

def technical_analysis_tool(df):

    close = df["close"]
    high = df["high"]
    low = df["low"]

    latest_price = float(
        close.iloc[-1]
    )

    sma20 = calculate_sma(
        close,
        20
    )

    sma50 = calculate_sma(
        close,
        50
    )

    sma200 = calculate_sma(
        close,
        200
    )

    ema20 = calculate_ema(
        close,
        20
    )

    rsi = calculate_rsi(
        close
    )

    macd, signal, hist = (
        calculate_macd(close)
    )

    atr = calculate_atr(
        high,
        low,
        close
    )

    upper, middle, lower = (
        calculate_bollinger_bands(
            close
        )
    )

    score = 0

    signals = []

    if latest_price > sma20.iloc[-1]:
        score += 10
        signals.append(
            "Price above SMA20"
        )

    if latest_price > sma50.iloc[-1]:
        score += 10
        signals.append(
            "Price above SMA50"
        )

    if (
        not sma200.empty
        and not sma200.isna().iloc[-1]
        and latest_price > sma200.iloc[-1]
    ):
        score += 15
        signals.append(
            "Price above SMA200"
        )

    if rsi.iloc[-1] > 60:
        score += 10
        signals.append(
            "RSI bullish"
        )

    if macd.iloc[-1] > signal.iloc[-1]:
        score += 15
        signals.append(
            "MACD bullish crossover"
        )

    trend = "Bullish"

    if score < 20:
        trend = "Bearish"

    elif score < 40:
        trend = "Neutral"

    support = float(
        close.tail(20).min()
    )

    resistance = float(
        close.tail(20).max()
    )

    return {
        "score": score,
        "trend": trend,
        "support": support,
        "resistance": resistance,
        "rsi": clean_number(rsi.iloc[-1]),
        "macd": clean_number(macd.iloc[-1]),
        "atr": clean_number(atr.iloc[-1]),
        "volatility": clean_number(calculate_volatility(close)),
        "drawdown": clean_number(calculate_drawdown(close)),
        "sma200": clean_number(sma200.iloc[-1]),
        "signals": signals
    }