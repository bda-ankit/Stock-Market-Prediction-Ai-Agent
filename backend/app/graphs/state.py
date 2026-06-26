from typing import TypedDict

import pandas as pd


class StockState(TypedDict, total=False):

    dataframe: pd.DataFrame

    news_text: str

    technical_analysis: dict

    news_analysis: dict

    risk_analysis: dict

    rf_prediction: dict

    xgb_prediction: dict

    lstm_prediction: dict

    llm_analysis: dict