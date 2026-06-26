from pydantic import BaseModel
from typing import List, Dict, Optional


class DateRange(BaseModel):
    from_date: str
    to_date: str


class TechnicalAnalysis(BaseModel):
    score: float
    trend: str

    support: float
    resistance: float

    rsi: Optional[float] = None
    macd: Optional[float] = None
    atr: Optional[float] = None

    volatility: float
    drawdown: float

    sma200: Optional[float] = None

    signals: List[str]


class NewsAnalysis(BaseModel):
    score: float
    classification: str


class EconomicAnalysis(BaseModel):
    score: float
    label: str


class MarketSentiment(BaseModel):
    indian_score: float
    indian_label: str

    global_score: float
    global_label: str


class PriceTarget(BaseModel):
    target_price: float
    probability: float
    confidence: float


class Risks(BaseModel):
    worst_case_estimate: float
    best_case_estimate: float

    key_risks: List[str]
    downside_scenarios: List[str]


class LLMAnalysis(BaseModel):
    model: str
    status: str

    recommendation: str
    summary: str

    reasoning: List[str]
    risk_notes: List[str]


class FinalAIScore(BaseModel):
    overall_score: float
    confidence: float


class AnalysisResponse(BaseModel):
    asset: str

    date_range: DateRange

    rows_analyzed: int

    current_price: float

    recommendation: str

    trend: str

    final_ai_score: FinalAIScore

    technical_analysis: TechnicalAnalysis

    news_analysis: NewsAnalysis

    market_sentiment: MarketSentiment

    economic_analysis: EconomicAnalysis

    price_targets: Dict[str, PriceTarget]

    risks: Risks

    llm_analysis: Optional[LLMAnalysis] = None

    explanation: str

    disclaimer: str