from __future__ import annotations

import math
import re
import json
from dataclasses import dataclass
from io import BytesIO, StringIO
from typing import Any
from urllib import error, request

import numpy as np
import pandas as pd


OLLAMA_URL = "http://127.0.0.1:11434/api/generate"
OLLAMA_MODEL = "deepseek-r1:8b"
REQUIRED_COLUMNS = ("date", "open", "high", "low", "close", "volume")
COLUMN_ALIASES = {
    "date": {"date", "tradingdate", "timestamp", "time", "pricedate", "tradedate"},
    "open": {"open", "openprice", "openingprice", "o"},
    "high": {"high", "highprice", "dayhigh", "h"},
    "low": {"low", "lowprice", "daylow", "l"},
    "close": {"close", "closeprice", "closingprice", "last", "lastprice", "ltp", "lasttradedprice", "adjclose", "adjustedclose"},
    "volume": {"volume", "vol", "quantity", "qty", "tradedqty", "totaltradedquantity", "totaltradedqty", "ttltrdqty", "shares", "sharestraded"},
}
NEGATIVE_COLUMN_HINTS = {
    "close": {"prevclose", "previousclose", "prevclosingprice"},
    "volume": {"value", "turnover", "trades", "nooftrades", "numberoftrades"},
}


@dataclass
class StaticContext:
    news_score: int = 8
    global_score: int = 4
    indian_score: int = 6
    economic_score: int = 3
    geopolitical_score: int = -2
    election_score: int = 1
    commodity_score: int = 0
    news_label: str = "Neutral to Positive"
    global_label: str = "Neutral / Mild Risk On"
    indian_label: str = "Constructive"
    economic_label: str = "Stable"
    geopolitical_label: str = "Mild Risk"
    election_label: str = "Limited Impact"
    commodity_label: str = "No strong correlation detected"


def analyze_uploaded_file(file_bytes: bytes, filename: str, asset: str, news_text: str = "") -> dict[str, Any]:
    df = _load_market_file(file_bytes, filename)
    df = _normalize_market_frame(df)
    asset_name = asset.strip() or _asset_from_filename(filename) or "Uploaded Asset"

    if len(df) < 30:
        raise ValueError("Please upload at least 30 rows of OHLCV data for a useful analysis.")

    indicators = _calculate_indicators(df)
    technical = _score_technical(indicators)
    context = _static_context()
    final_score = _weighted_score(technical["score"], context)
    recommendation = _recommendation(final_score)
    current_price = float(indicators["close"].iloc[-1])
    atr = float(indicators["atr_14"].iloc[-1]) if not pd.isna(indicators["atr_14"].iloc[-1]) else current_price * 0.025
    volatility = _annualized_volatility(indicators["close"])
    price_targets = _price_targets(current_price, atr, technical["score"], final_score)
    risks = _risk_analysis(current_price, atr, volatility, technical)

    result = {
        "asset": asset_name,
        "currentPrice": round(current_price, 2),
        "trend": technical["trend"],
        "rowsAnalyzed": int(len(indicators)),
        "dateRange": {
            "from": indicators["date"].iloc[0].strftime("%Y-%m-%d"),
            "to": indicators["date"].iloc[-1].strftime("%Y-%m-%d"),
        },
        "technicalAnalysis": {
            "score": technical["score"],
            "signals": technical["signals"],
            "support": round(float(indicators["low"].tail(20).min()), 2),
            "resistance": round(float(indicators["high"].tail(20).max()), 2),
            "rsi": _safe_round(indicators["rsi_14"].iloc[-1]),
            "macd": _safe_round(indicators["macd"].iloc[-1]),
            "macdSignal": _safe_round(indicators["macd_signal"].iloc[-1]),
            "atr": round(atr, 2),
            "volatility": round(volatility * 100, 2),
            "drawdown": round(_max_drawdown(indicators["close"]) * 100, 2),
            "sma20": _safe_round(indicators["sma_20"].iloc[-1]),
            "sma50": _safe_round(indicators["sma_50"].iloc[-1]),
            "sma200": _safe_round(indicators["sma_200"].iloc[-1]),
            "ema20": _safe_round(indicators["ema_20"].iloc[-1]),
            "ema50": _safe_round(indicators["ema_50"].iloc[-1]),
        },
        "newsAnalysis": {
            "score": context.news_score,
            "classification": "User supplied news context" if news_text.strip() else context.news_label,
            "items": _news_items(news_text),
        },
        "marketSentiment": {
            "globalScore": context.global_score,
            "globalLabel": context.global_label,
            "indianScore": context.indian_score,
            "indianLabel": context.indian_label,
        },
        "economicAnalysis": {"score": context.economic_score, "label": context.economic_label},
        "geopoliticalAnalysis": {"score": context.geopolitical_score, "label": context.geopolitical_label},
        "electionImpact": {"score": context.election_score, "label": context.election_label},
        "commodityCorrelation": {"score": context.commodity_score, "label": context.commodity_label},
        "finalAiScore": {
            "overallScore": round(final_score, 2),
            "confidence": _confidence(final_score, len(indicators), volatility),
        },
        "recommendation": recommendation,
        "priceTargets": price_targets,
        "risks": risks,
        "explanation": _explanation(technical, context, final_score, recommendation),
        "disclaimer": "This is probability-based analysis, not financial advice. Future prices and returns are never guaranteed.",
    }
    result["llmAnalysis"] = _deep_llm_analysis(result, indicators, news_text)
    return result


def _load_market_file(file_bytes: bytes, filename: str) -> pd.DataFrame:
    lower_name = filename.lower()
    if lower_name.endswith(".csv"):
        text = file_bytes.decode("utf-8-sig")
        return pd.read_csv(StringIO(text), sep=None, engine="python")
    if lower_name.endswith((".xlsx", ".xlsm", ".xltx", ".xltm")):
        return pd.read_excel(BytesIO(file_bytes), engine="openpyxl")
    if lower_name.endswith(".xls"):
        return pd.read_excel(BytesIO(file_bytes))
    raise ValueError("Unsupported file type. Upload a CSV, XLS, or XLSX file.")


def _normalize_market_frame(df: pd.DataFrame) -> pd.DataFrame:
    normalized = df.copy()
    column_mapping = _identify_market_columns(normalized.columns)

    missing = [column for column in REQUIRED_COLUMNS if column not in column_mapping]
    if missing:
        found = ", ".join(str(column) for column in normalized.columns)
        expected = "date/open/high/low/close/volume columns. NSE quote headers like DATE, OPEN, HIGH, LOW, CLOSE, VOLUME are supported."
        raise ValueError(f"Could not identify: {', '.join(missing)}. Expected {expected} Found columns: {found}")

    normalized = normalized.rename(columns={source: target for target, source in column_mapping.items()})
    normalized = normalized[list(REQUIRED_COLUMNS)]
    normalized["date"] = _parse_market_dates(normalized["date"])
    for column in ["open", "high", "low", "close", "volume"]:
        normalized[column] = normalized[column].map(_clean_number)

    normalized = normalized.dropna(subset=["date", "open", "high", "low", "close", "volume"])
    normalized = normalized.sort_values("date").reset_index(drop=True)
    if normalized.empty:
        raise ValueError("No valid OHLCV rows were found in the uploaded file.")
    return normalized


def _identify_market_columns(columns: pd.Index) -> dict[str, Any]:
    available = list(columns)
    normalized_names = {column: _compact_column_name(column) for column in available}
    mapping: dict[str, Any] = {}
    used: set[Any] = set()

    for logical_name in REQUIRED_COLUMNS:
        best_column = None
        best_score = 0
        for column, compact_name in normalized_names.items():
            if column in used:
                continue
            score = _column_match_score(logical_name, compact_name)
            if score > best_score:
                best_column = column
                best_score = score
        if best_column is not None and best_score >= 60:
            mapping[logical_name] = best_column
            used.add(best_column)

    return mapping


def _compact_column_name(column: Any) -> str:
    name = str(column).strip().lower()
    name = name.replace("%", "percent")
    return re.sub(r"[^a-z0-9]", "", name)


def _column_match_score(logical_name: str, compact_name: str) -> int:
    if compact_name in NEGATIVE_COLUMN_HINTS.get(logical_name, set()):
        return 0
    if compact_name == logical_name:
        return 120
    if logical_name == "close" and compact_name == "ltp":
        return 92
    aliases = COLUMN_ALIASES[logical_name]
    if compact_name in aliases:
        return 100
    if any(compact_name.startswith(alias) for alias in aliases if len(alias) >= 4):
        return 88
    if any(alias in compact_name for alias in aliases if len(alias) >= 4):
        return 78
    if logical_name == "date" and compact_name.endswith("date"):
        return 85
    if logical_name == "volume" and "volume" in compact_name:
        return 85
    if logical_name == "close" and compact_name.endswith("close") and "prev" not in compact_name:
        return 82
    return 0


def _parse_market_dates(values: pd.Series) -> pd.Series:
    text_values = values.astype(str).str.strip()
    parsed = pd.Series(pd.NaT, index=values.index, dtype="datetime64[ns]")
    for date_format in ("%d-%b-%y", "%d-%b-%Y", "%d-%m-%Y", "%d/%m/%Y", "%Y-%m-%d", "%Y/%m/%d"):
        remaining = parsed.isna()
        if not remaining.any():
            break
        parsed.loc[remaining] = pd.to_datetime(text_values.loc[remaining], format=date_format, errors="coerce")
    remaining = parsed.isna()
    if remaining.any():
        parsed.loc[remaining] = pd.to_datetime(text_values.loc[remaining], dayfirst=True, errors="coerce")
    return parsed


def _clean_number(value: Any) -> float:
    if pd.isna(value):
        return float("nan")
    if isinstance(value, (int, float, np.number)):
        return float(value)
    cleaned = str(value).strip().replace(",", "")
    cleaned = re.sub(r"(?i)\b(rs|inr)\.?\b", "", cleaned)
    cleaned = re.sub(r"[^0-9.\-]", "", cleaned)
    if cleaned in {"", "-", "--", ".", "-."}:
        return float("nan")
    return float(cleaned)


def _asset_from_filename(filename: str) -> str | None:
    basename = str(filename).replace("\\", "/").split("/")[-1]
    match = re.search(r"Quote-Equity-(?P<symbol>.+?)-EQ-\d{2}-\d{2}-\d{4}-\d{2}-\d{2}-\d{4}", basename, re.IGNORECASE)
    if match:
        return match.group("symbol").upper()
    return None


def _calculate_indicators(df: pd.DataFrame) -> pd.DataFrame:
    out = df.copy()
    close = out["close"]
    high = out["high"]
    low = out["low"]

    out["sma_20"] = close.rolling(20).mean()
    out["sma_50"] = close.rolling(50).mean()
    out["sma_200"] = close.rolling(200).mean()
    out["ema_20"] = close.ewm(span=20, adjust=False).mean()
    out["ema_50"] = close.ewm(span=50, adjust=False).mean()

    delta = close.diff()
    gain = delta.clip(lower=0).rolling(14).mean()
    loss = -delta.clip(upper=0).rolling(14).mean()
    rs = gain / loss.replace(0, np.nan)
    out["rsi_14"] = 100 - (100 / (1 + rs))
    out.loc[(loss == 0) & (gain > 0), "rsi_14"] = 100
    out.loc[(loss == 0) & (gain == 0), "rsi_14"] = 50

    ema_12 = close.ewm(span=12, adjust=False).mean()
    ema_26 = close.ewm(span=26, adjust=False).mean()
    out["macd"] = ema_12 - ema_26
    out["macd_signal"] = out["macd"].ewm(span=9, adjust=False).mean()
    out["macd_histogram"] = out["macd"] - out["macd_signal"]

    bb_middle = out["sma_20"]
    bb_std = close.rolling(20).std()
    out["bb_upper"] = bb_middle + (2 * bb_std)
    out["bb_lower"] = bb_middle - (2 * bb_std)

    previous_close = close.shift(1)
    true_range = pd.concat(
        [(high - low), (high - previous_close).abs(), (low - previous_close).abs()],
        axis=1,
    ).max(axis=1)
    out["atr_14"] = true_range.rolling(14).mean()
    return out


def _score_technical(df: pd.DataFrame) -> dict[str, Any]:
    latest = df.iloc[-1]
    previous = df.iloc[-2]
    score = 0
    signals: list[str] = []

    def add(points: int, message: str) -> None:
        nonlocal score
        score += points
        signals.append(message)

    close = latest["close"]
    if not pd.isna(latest["sma_20"]):
        add(12 if close > latest["sma_20"] else -12, "Price is above SMA 20" if close > latest["sma_20"] else "Price is below SMA 20")
    if not pd.isna(latest["sma_50"]):
        add(15 if close > latest["sma_50"] else -15, "Price is above SMA 50" if close > latest["sma_50"] else "Price is below SMA 50")
    if not pd.isna(latest["sma_200"]):
        add(18 if close > latest["sma_200"] else -18, "Price is above SMA 200" if close > latest["sma_200"] else "Price is below SMA 200")

    if latest["ema_20"] > latest["ema_50"]:
        add(12, "EMA 20 is above EMA 50")
    else:
        add(-12, "EMA 20 is below EMA 50")

    if not pd.isna(latest["rsi_14"]):
        if latest["rsi_14"] > 70:
            add(-12, "RSI is overbought")
        elif latest["rsi_14"] < 30:
            add(8, "RSI is oversold and may rebound")
        elif 45 <= latest["rsi_14"] <= 65:
            add(8, "RSI is in a constructive neutral range")

    if latest["macd"] > latest["macd_signal"]:
        add(12, "MACD is above signal line")
    else:
        add(-12, "MACD is below signal line")

    if latest["close"] > previous["close"]:
        add(8, "Latest close is higher than previous close")
    else:
        add(-8, "Latest close is lower than previous close")

    volume_average = df["volume"].tail(20).mean()
    if latest["volume"] > volume_average and latest["close"] > previous["close"]:
        add(8, "Up move has above-average volume")
    elif latest["volume"] > volume_average and latest["close"] < previous["close"]:
        add(-8, "Down move has above-average volume")

    score = max(-100, min(100, score))
    if score >= 35:
        trend = "Bullish"
    elif score <= -25:
        trend = "Bearish"
    else:
        trend = "Neutral"
    return {"score": score, "signals": signals, "trend": trend}


def _static_context() -> StaticContext:
    return StaticContext()


def _news_items(news_text: str) -> list[str]:
    cleaned = news_text.strip()
    if not cleaned:
        return [
            "No user news context was provided.",
            "Ollama deep analysis will rely mainly on uploaded price/volume data.",
        ]
    sentences = re.split(r"(?<=[.!?])\s+", cleaned)
    items = [sentence.strip() for sentence in sentences if sentence.strip()]
    return items[:5] or [cleaned[:500]]


def _weighted_score(technical_score: int, context: StaticContext) -> float:
    technical_0_100 = (technical_score + 100) / 2
    news_0_100 = _range_to_percent(context.news_score, -30, 30)
    indian_0_100 = _range_to_percent(context.indian_score, -20, 20)
    global_0_100 = _range_to_percent(context.global_score, -20, 20)
    economic_0_100 = _range_to_percent(context.economic_score, -20, 20)
    geopolitical_0_100 = _range_to_percent(context.geopolitical_score, -20, 20)
    election_0_100 = _range_to_percent(context.election_score, -15, 15)
    commodity_0_100 = _range_to_percent(context.commodity_score, -15, 15)

    return (
        technical_0_100 * 0.40
        + news_0_100 * 0.20
        + indian_0_100 * 0.10
        + global_0_100 * 0.10
        + economic_0_100 * 0.10
        + geopolitical_0_100 * 0.05
        + election_0_100 * 0.03
        + commodity_0_100 * 0.02
    )


def _range_to_percent(value: float, low: float, high: float) -> float:
    return max(0, min(100, ((value - low) / (high - low)) * 100))


def _recommendation(score: float) -> str:
    if score > 75:
        return "STRONG BUY"
    if score >= 60:
        return "BUY"
    if score >= 45:
        return "HOLD"
    if score >= 30:
        return "SELL"
    return "STRONG SELL"


def _confidence(score: float, rows: int, volatility: float) -> int:
    data_quality = min(30, rows / 8)
    score_distance = min(35, abs(score - 50) * 1.1)
    volatility_penalty = min(20, volatility * 30)
    confidence = 45 + data_quality + score_distance - volatility_penalty
    return int(max(35, min(92, round(confidence))))


def _price_targets(current_price: float, atr: float, technical_score: int, final_score: float) -> dict[str, dict[str, float]]:
    bias = (final_score - 50) / 50
    tech_bias = technical_score / 100
    combined_bias = (bias * 0.7) + (tech_bias * 0.3)
    horizons = {
        "1Week": (1, 0.55),
        "1Month": (2.2, 0.60),
        "3Month": (4.0, 0.64),
        "6Month": (6.2, 0.67),
        "12Month": (9.0, 0.70),
    }
    targets: dict[str, dict[str, float]] = {}
    for name, (atr_multiplier, base_probability) in horizons.items():
        projected_move = atr * atr_multiplier * combined_bias
        target = max(0.01, current_price + projected_move)
        probability = max(35, min(82, (base_probability + abs(combined_bias) * 0.16) * 100))
        confidence = max(35, min(88, probability - (atr_multiplier * 1.7)))
        targets[name] = {
            "targetPrice": round(target, 2),
            "probability": round(probability, 1),
            "confidence": round(confidence, 1),
        }
    return targets


def _risk_analysis(current_price: float, atr: float, volatility: float, technical: dict[str, Any]) -> dict[str, Any]:
    downside_multiplier = 3.5 if technical["score"] >= 0 else 5.0
    upside_multiplier = 5.0 if technical["score"] >= 0 else 3.0
    return {
        "keyRisks": [
            "Uploaded data may not include corporate actions such as splits, bonuses, or dividends.",
            "Static news and macro scores are placeholders until live scraping is added.",
            "High volatility can invalidate short-term targets quickly.",
            "Unexpected RBI, budget, regulatory, earnings, or global risk events can change sentiment.",
        ],
        "downsideScenarios": [
            "Break below recent support with rising volume.",
            "MACD deterioration with RSI falling below 40.",
            "Broader Indian market weakness or India VIX spike.",
        ],
        "worstCaseEstimate": round(max(0.01, current_price - atr * downside_multiplier * (1 + volatility)), 2),
        "bestCaseEstimate": round(current_price + atr * upside_multiplier * (1 + volatility), 2),
    }


def _explanation(technical: dict[str, Any], context: StaticContext, final_score: float, recommendation: str) -> str:
    return (
        f"The model combines an uploaded OHLCV technical score of {technical['score']} with static placeholder "
        f"news, market, macro, geopolitical, election, and commodity scores. The weighted output is {final_score:.2f}, "
        f"which maps to {recommendation}. Treat this as a probability-based dashboard result; the static inputs should "
        "be replaced by live scraping feeds before using it for production decisions."
    )


def _deep_llm_analysis(result: dict[str, Any], indicators: pd.DataFrame, news_text: str) -> dict[str, Any]:
    prompt = _llm_prompt(result, indicators, news_text)
    try:
        response_text = _call_ollama(prompt)
    except Exception as exc:
        return {
            "status": "unavailable",
            "model": OLLAMA_MODEL,
            "summary": f"Ollama deep analysis was skipped: {exc}",
            "recommendation": result["recommendation"],
            "reasoning": [],
            "priceView": result["priceTargets"],
            "riskNotes": result["risks"]["keyRisks"],
        }

    parsed = _extract_json(response_text)
    if parsed is None:
        return {
            "status": "raw",
            "model": OLLAMA_MODEL,
            "summary": response_text.strip()[:4000],
            "recommendation": result["recommendation"],
            "reasoning": [],
            "priceView": result["priceTargets"],
            "riskNotes": result["risks"]["keyRisks"],
        }
    parsed.setdefault("status", "ok")
    parsed.setdefault("model", OLLAMA_MODEL)
    return parsed


def _llm_prompt(result: dict[str, Any], indicators: pd.DataFrame, news_text: str) -> str:
    latest_rows = indicators.tail(20).copy()
    latest_rows["date"] = latest_rows["date"].dt.strftime("%Y-%m-%d")
    fields = [
        "date",
        "open",
        "high",
        "low",
        "close",
        "volume",
        "sma_20",
        "sma_50",
        "ema_20",
        "ema_50",
        "rsi_14",
        "macd",
        "macd_signal",
        "atr_14",
    ]
    market_rows = latest_rows[fields].round(4).where(pd.notna(latest_rows[fields]), None).to_dict("records")
    context = {
        "asset": result["asset"],
        "dateRange": result["dateRange"],
        "rowsAnalyzed": result["rowsAnalyzed"],
        "currentPrice": result["currentPrice"],
        "technicalAnalysis": result["technicalAnalysis"],
        "deterministicScore": result["finalAiScore"],
        "deterministicRecommendation": result["recommendation"],
        "deterministicPriceTargets": result["priceTargets"],
        "riskRange": {
            "worstCaseEstimate": result["risks"]["worstCaseEstimate"],
            "bestCaseEstimate": result["risks"]["bestCaseEstimate"],
        },
        "latestCalculatedRows": market_rows,
        "newsText": news_text.strip()[:5000],
    }
    return (
        "You are a disciplined Indian equity analyst. Use the supplied calculated OHLCV indicators and user news context. "
        "Do not invent live news or market data. Do not recalculate arithmetic in a way that contradicts the supplied values. "
        "Give an unbiased probabilistic view and clearly separate evidence from uncertainty. "
        "Return only valid JSON with keys: summary, recommendation, confidence, reasoning, priceView, riskNotes, newsImpact. "
        "priceView must contain 1Week, 1Month, 3Month, 6Month, 12Month objects with targetPrice, probability, confidence, rationale. "
        f"Context JSON:\n{json.dumps(context, ensure_ascii=False)}"
    )


def _call_ollama(prompt: str) -> str:
    payload = {
        "model": OLLAMA_MODEL,
        "prompt": prompt,
        "stream": False,
        "options": {
            "temperature": 0.1,
            "top_p": 0.9,
            "num_ctx": 8192,
        },
    }
    data = json.dumps(payload).encode("utf-8")
    req = request.Request(OLLAMA_URL, data=data, headers={"Content-Type": "application/json"}, method="POST")
    try:
        with request.urlopen(req, timeout=120) as resp:
            body = json.loads(resp.read().decode("utf-8"))
    except error.URLError as exc:
        raise RuntimeError("make sure Ollama is running at 127.0.0.1:11434 and the model deepseek-r1:8b is available") from exc
    return str(body.get("response", ""))


def _extract_json(text: str) -> dict[str, Any] | None:
    cleaned = re.sub(r"<think>.*?</think>", "", text, flags=re.DOTALL | re.IGNORECASE).strip()
    fenced = re.search(r"```(?:json)?\s*(\{.*?\})\s*```", cleaned, flags=re.DOTALL)
    candidate = fenced.group(1) if fenced else cleaned
    if not candidate.startswith("{"):
        start = candidate.find("{")
        end = candidate.rfind("}")
        if start == -1 or end == -1 or end <= start:
            return None
        candidate = candidate[start : end + 1]
    try:
        parsed = json.loads(candidate)
    except json.JSONDecodeError:
        return None
    return parsed if isinstance(parsed, dict) else None


def _annualized_volatility(close: pd.Series) -> float:
    returns = close.pct_change().dropna()
    if returns.empty:
        return 0.0
    return float(returns.std() * math.sqrt(252))


def _max_drawdown(close: pd.Series) -> float:
    running_max = close.cummax()
    drawdown = (close - running_max) / running_max
    return float(drawdown.min())


def _safe_round(value: Any) -> float | None:
    if pd.isna(value):
        return None
    return round(float(value), 2)
