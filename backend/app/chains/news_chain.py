import json

from langchain_core.prompts import (
    ChatPromptTemplate
)

from services.llm import llm


NEWS_PROMPT = """
Analyze the following stock news.

Provide:

- sentiment
- key positives
- key negatives
- overall market impact

News:

{news}
"""


prompt = ChatPromptTemplate.from_template(
    NEWS_PROMPT
)

news_chain = prompt | llm


async def run_news_chain(
    news: str
):

    result = await news_chain.ainvoke(
        {
            "news": news
        }
    )

    return result.content