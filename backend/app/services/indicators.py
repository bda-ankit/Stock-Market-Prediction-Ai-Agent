import numpy as np
import pandas as pd


def calculate_sma(
    series: pd.Series,
    period: int
) -> pd.Series:
    return series.rolling(period).mean()


def calculate_ema(
    series: pd.Series,
    period: int
) -> pd.Series:
    return series.ewm(
        span=period,
        adjust=False
    ).mean()


def calculate_rsi(
    close: pd.Series,
    period: int = 14
) -> pd.Series:

    delta = close.diff()

    gain = delta.where(
        delta > 0,
        0.0
    )

    loss = -delta.where(
        delta < 0,
        0.0
    )

    avg_gain = gain.rolling(
        period
    ).mean()

    avg_loss = loss.rolling(
        period
    ).mean()

    rs = avg_gain / avg_loss

    rsi = 100 - (
        100 / (1 + rs)
    )

    return rsi


def calculate_macd(
    close: pd.Series
):

    ema12 = calculate_ema(
        close,
        12
    )

    ema26 = calculate_ema(
        close,
        26
    )

    macd = ema12 - ema26

    signal = calculate_ema(
        macd,
        9
    )

    histogram = macd - signal

    return (
        macd,
        signal,
        histogram
    )


def calculate_bollinger_bands(
    close: pd.Series,
    period: int = 20
):

    sma = calculate_sma(
        close,
        period
    )

    std = close.rolling(
        period
    ).std()

    upper = sma + (2 * std)

    lower = sma - (2 * std)

    return (
        upper,
        sma,
        lower
    )


def calculate_atr(
    high: pd.Series,
    low: pd.Series,
    close: pd.Series,
    period: int = 14
):

    previous_close = close.shift()

    tr1 = high - low

    tr2 = (
        high - previous_close
    ).abs()

    tr3 = (
        low - previous_close
    ).abs()

    true_range = pd.concat(
        [tr1, tr2, tr3],
        axis=1
    ).max(axis=1)

    atr = true_range.rolling(
        period
    ).mean()

    return atr


def calculate_volatility(
    close: pd.Series
):

    returns = close.pct_change()

    volatility = (
        returns.std()
        * np.sqrt(252)
        * 100
    )

    return float(volatility)


def calculate_drawdown(
    close: pd.Series
):

    rolling_max = close.cummax()

    drawdown = (
        (close - rolling_max)
        / rolling_max
    ) * 100

    return float(drawdown.min())