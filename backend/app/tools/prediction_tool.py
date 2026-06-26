import pandas as pd

from sklearn.ensemble import RandomForestRegressor


def prediction_tool(df: pd.DataFrame):

    df = df.copy()

    close = df["close"]

    df["returns"] = close.pct_change()

    df["sma20"] = close.rolling(20).mean()

    df["sma50"] = close.rolling(50).mean()

    df["momentum"] = close / close.shift(10)

    df["volatility"] = (
        df["returns"]
        .rolling(20)
        .std()
    )

    df["target"] = close.shift(-1)

    df = df.dropna()

    if len(df) < 100:

        return {
            "model": "RandomForest",
            "prediction": float(close.iloc[-1]),
            "confidence": 0
        }

    features = [
        "returns",
        "sma20",
        "sma50",
        "momentum",
        "volatility"
    ]

    X = df[features]

    y = df["target"]

    model = RandomForestRegressor(
        n_estimators=300,
        max_depth=8,
        random_state=42
    )

    model.fit(X, y)

    predicted_price = float(
        model.predict(
            X.tail(1)
        )[0]
    )

    confidence = min(
        abs(
            predicted_price
            - close.iloc[-1]
        )
        /
        close.iloc[-1]
        * 100
        * 10,
        95
    )

    return {
        "model": "RandomForest",
        "prediction": round(
            predicted_price,
            2
        ),
        "confidence": round(
            confidence,
            2
        )
    }