from tools.technical_tool import (
    technical_analysis_tool
)

from tools.sentiment_tool import (
    sentiment_tool
)

from tools.risk_tool import (
    risk_tool
)

from chains.news_chain import (
    run_news_chain
)

from chains.final_chain import (
    run_final_chain
)

from tools.prediction_tool import (
    prediction_tool
)

from tools.xgboost_tool import (
    xgboost_tool
)

from tools.lstm_tool import (
    lstm_tool
)

async def technical_node(state):

    technical = technical_analysis_tool(
        state["dataframe"]
    )

    print("\n===== TECHNICAL NODE =====")
    print(type(technical))
    print(technical)

    return {
        "technical_analysis": technical
    }


async def news_node(state):

    sentiment = sentiment_tool(
        state.get(
            "news_text",
            ""
        )
    )

    news_llm = (
        await run_news_chain(
            state.get(
                "news_text",
                ""
            )
        )
    )

    return {
        "news_analysis": {
            **sentiment,
            "llm_view": news_llm
        }
    }


async def risk_node(state):

    print("\n===== RISK NODE =====")
    print(state.keys())

    print("technical_analysis:")
    print(state.get("technical_analysis"))

    risk = risk_tool(
        state["technical_analysis"]
    )

    return {
        "risk_analysis": risk
    }

# async def prediction_node(state):

#     prediction = prediction_tool(
#         state["dataframe"]
#     )

#     print("\n===== PREDICTION NODE =====")
#     print(type(prediction))
#     print(prediction)

#     print("\n===== DATAFRAME COLUMNS =====")
#     print(state["dataframe"].columns.tolist())

#     df = state["dataframe"]

#     print(df.columns.tolist())

#     if "Close" in df.columns:
#         current_price = float(df["Close"].iloc[-1])

#     elif "close" in df.columns:
#         current_price = float(df["close"].iloc[-1])

#     elif "CLOSE" in df.columns:
#         current_price = float(df["CLOSE"].iloc[-1])

#     else:
#         raise ValueError(
#             f"Close column not found. Available columns: {df.columns.tolist()}"
#         )

#     predicted_price = prediction["next_day_price"]

#     direction = prediction["direction"]

#     confidence = prediction["confidence"]

#     move_percent = round(
#         (
#             (predicted_price - current_price)
#             / current_price
#         ) * 100,
#         2
#     )

#     return {
#         "prediction_analysis": {
#             "current_price": current_price,
#             "predicted_price": predicted_price,
#             "predicted_move_percent": move_percent,
#             "direction": direction,
#             "confidence": confidence
#         }
#     }

async def rf_prediction_node(state):

    result = prediction_tool(
        state["dataframe"]
    )

    print(
        "\n===== RF PREDICTION ====="
    )

    print(result)

    return {
        "rf_prediction": result
    }

async def xgb_prediction_node(state):

    result = xgboost_tool(
        state["dataframe"]
    )

    print(
        "\n===== XGBOOST PREDICTION ====="
    )

    print(result)

    return {
        "xgb_prediction": result
    }


async def lstm_prediction_node(state):

    result = lstm_tool(
        state["dataframe"]
    )

    print(
        "\n===== LSTM PREDICTION ====="
    )

    print(result)

    return {
        "lstm_prediction": result
    }


async def final_node(state):

    result = await run_final_chain(
        technical=state["technical_analysis"],
        news=state["news_analysis"],
        risk=state["risk_analysis"],
        rf_prediction=state["rf_prediction"],
        xgb_prediction=state["xgb_prediction"],
        lstm_prediction=state["lstm_prediction"]
    )

    llm_result = result.model_dump()

    llm_result["rf_prediction"] = (
        state["rf_prediction"]
    )

    llm_result["xgb_prediction"] = (
        state["xgb_prediction"]
    )

    llm_result["lstm_prediction"] = (
        state["lstm_prediction"]
    )

    return {
        "llm_analysis": llm_result
    }

# new changes