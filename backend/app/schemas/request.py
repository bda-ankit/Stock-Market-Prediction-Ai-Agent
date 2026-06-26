from pydantic import BaseModel


class AnalyzeRequest(BaseModel):
    asset: str = ""
    news_text: str = ""