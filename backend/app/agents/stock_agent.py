from graphs.stock_graph import (
    stock_graph
)


class StockAgent:

    async def analyze(
        self,
        dataframe,
        news_text=""
    ):

        state = {
            "dataframe": dataframe,
            "news_text": news_text
        }

        result = (
            await stock_graph.ainvoke(
                state
            )
        )

        return {
            "technical_analysis": result.get("technical_analysis"),
            "news_analysis": result.get("news_analysis"),
            "risk_analysis": result.get("risk_analysis"),
            "llm_analysis": result.get("llm_analysis")
        }


stock_agent = StockAgent()