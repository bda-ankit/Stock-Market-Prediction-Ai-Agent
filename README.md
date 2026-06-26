# Stock Market Prediction AI Agent

A local full-stack website for uploading Indian-market OHLCV data and generating a probability-based investment dashboard.

## Features

- Upload CSV, XLS, or XLSX files.
- Accepts NSE quote files named like `Quote-Equity-KAMDHENU-EQ-16-03-2026-16-06-2026.csv`.
- Dynamically identifies common date, open, high, low, close, and volume column names.
- Supports headers such as `DATE`, `OPEN`, `HIGH`, `LOW`, `CLOSE`, `LTP`, `VOLUME`, `Total Traded Quantity`, `VOL`, and similar variants.
- Extra columns are ignored, including `SERIES`, `PREV. CLOSE`, `VWAP`, `52W H`, `52W L`, `VALUE`, and `NO. OF TRADES`.
- Calculates SMA 20/50/200, EMA 20/50, RSI, MACD, Bollinger Bands, ATR, volatility, support, resistance, and drawdown.
- Produces weighted AI score, recommendation, price targets, risks, and explanation.
- Accepts pasted news and market context from the UI.
- Sends the calculated metrics, recent OHLCV rows, deterministic targets, and news context to local Ollama model `deepseek-r1:8b` for a second-pass analysis.

## Run

Use Python 3.10+:

```powershell
pip install -r requirements.txt
```

```powershell
python backend/server.py
```

Then open:

```text
http://127.0.0.1:8000
```

For local DeepSeek feedback, make sure Ollama is running and the model is available:

```powershell
ollama pull deepseek-r1:8b
ollama serve
```

If you already have Ollama running, the app calls:

```text
http://127.0.0.1:11434/api/generate
```

If Python is not on PATH in this Codex workspace, this bundled runtime works:

```powershell
& 'C:\Users\Admin\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe' backend/server.py
```

## Accuracy Note

The app keeps numeric calculations in Pandas for accuracy. The LLM receives those calculated values plus news text and recent rows for interpretation, probabilistic feedback, and risk review. It should not be treated as a fine-tuned price oracle.

## Live Scraping Later

Replace `_static_context()` in `backend/analyzer.py` with real scrapers or API calls. Keep the returned score ranges the same:

- News: `-30` to `+30`
- Global market: `-20` to `+20`
- Indian market: `-20` to `+20`
- Economic: `-20` to `+20`
- Geopolitical: `-20` to `+20`
- Election: `-15` to `+15`
- Commodity: `-15` to `+15`

## Disclaimer

This application provides probability-based analysis only. It does not guarantee future returns or prices and is not financial advice.
