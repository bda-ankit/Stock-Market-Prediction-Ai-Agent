import json

from langchain_core.prompts import ChatPromptTemplate

from agents.prompts import (
    TECHNICAL_ANALYSIS_PROMPT
)

from schemas.llm_response import (
    LLMAnalysisResponse
)

from services.llm import llm


structured_llm = llm.with_structured_output(
    LLMAnalysisResponse
)


prompt = ChatPromptTemplate.from_template(
    TECHNICAL_ANALYSIS_PROMPT
)


technical_chain = (
    prompt
    | structured_llm
)


async def run_technical_chain(
    technical_data: dict
):

    result = await technical_chain.ainvoke(
        {
            "technical_data": json.dumps(
                technical_data,
                indent=2
            )
        }
    )

    return result