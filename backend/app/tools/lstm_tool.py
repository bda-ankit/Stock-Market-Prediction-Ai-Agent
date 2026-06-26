import numpy as np
import pandas as pd

from sklearn.preprocessing import MinMaxScaler

from tensorflow.keras.models import Sequential

from tensorflow.keras.layers import (
    Dense,
    LSTM
)

def lstm_tool(df: pd.DataFrame):

    close = (
        df["close"]
        .values
        .reshape(-1, 1)
    )

    if len(close) < 100:

        return {
            "model": "LSTM",
            "prediction": float(close[-1]),
            "confidence": 0
        }

    scaler = MinMaxScaler()

    scaled = scaler.fit_transform(
        close
    )

    X = []

    y = []

    lookback = 20

    for i in range(
        lookback,
        len(scaled)
    ):

        X.append(
            scaled[
                i - lookback:i
            ]
        )

        y.append(
            scaled[i]
        )

    X = np.array(X)

    y = np.array(y)

    model = Sequential()

    model.add(
        LSTM(
            50,
            input_shape=(
                X.shape[1],
                X.shape[2]
            )
        )
    )

    model.add(
        Dense(1)
    )

    model.compile(
        optimizer="adam",
        loss="mse"
    )

    model.fit(
        X,
        y,
        epochs=10,
        batch_size=16,
        verbose=0
    )

    prediction = model.predict(
        X[-1:]
    )

    predicted_price = scaler.inverse_transform(
        prediction
    )[0][0]

    current_price = float(
        close[-1][0]
    )

    confidence = min(
        abs(
            predicted_price
            - current_price
        )
        /
        current_price
        * 100
        * 10,
        95
    )

    return {
        "model": "LSTM",
        "prediction": round(float(predicted_price), 2),
        "confidence": round(float(confidence), 2),
        "direction": (
            "UP"
            if predicted_price > current_price
            else "DOWN"
        )
    }