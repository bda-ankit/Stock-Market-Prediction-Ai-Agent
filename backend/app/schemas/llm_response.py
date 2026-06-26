from typing import List

from pydantic import BaseModel

class LLMAnalysisResponse(BaseModel):

    recommendation: str

    confidence: int

    summary: str

    reasoning: list[str]

    riskNotes: list[str]

    predictedNextDayPrice: float

    predictedMovePercent: float

    nextDayOutlook: str

    outlook1Week: str

    outlook1Month: str

    outlook3Month: str