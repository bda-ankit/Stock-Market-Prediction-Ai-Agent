import json

from langchain_core.prompts import (
    ChatPromptTemplate
)

from services.llm import llm

from schemas.llm_response import (
    LLMAnalysisResponse
)


structured_llm = (
    llm.with_structured_output(
        LLMAnalysisResponse
    )
)

from agents.prompts import FINAL_ANALYSIS_PROMPT


# FINAL_PROMPT = """
# You are a professional stock analyst.

# Technical Analysis:

# {technical}

# News Analysis:

# {news}

# Risk Analysis:y

# {risk}

# Provide:

# - Recommendation
# - Confidence
# - Summary
# - Reasoning
# - Risk Notes
# """


prompt = ChatPromptTemplate.from_template(
    FINAL_ANALYSIS_PROMPT
)

final_chain = (
    prompt
    | structured_llm
)


async def run_final_chain(
    technical,
    news,
    risk,
    rf_prediction,
    xgb_prediction,
    lstm_prediction
):
    
    result = await final_chain.ainvoke(
        {
            "technical": json.dumps(
                technical,
                indent=2
            ),
            "news": json.dumps(
                news,
                indent=2
            ),
            "risk": json.dumps(
                risk,
                indent=2
            ),
            "rf_prediction": json.dumps(
                rf_prediction,
                indent=2
            ),
            "xgb_prediction": json.dumps(
                xgb_prediction,
                indent=2
            ),
            "lstm_prediction": json.dumps(
                lstm_prediction,
                indent=2
            )
        }
    )

    return result

