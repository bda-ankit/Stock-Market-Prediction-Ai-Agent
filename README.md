# Stock Market Prediction AI

A local, full-stack dashboard for analyzing uploaded Indian-market OHLCV data (Open, High, Low, Close, Volume). Upload a CSV or Excel export, optionally add your own news context, and receive technical indicators, a probability-weighted recommendation, price scenarios, risk notes, and an optional local-LLM interpretation.

> **Important:** This project is for research and educational analysis. It does not provide investment advice, guarantee prices or returns, or replace due diligence.

## What is currently runnable

The production-ready local workflow is:

`Browser → backend/server.py → backend/analyzer.py → JSON dashboard response`

It serves the static frontend and accepts file uploads at `POST /api/analyze`. It works without an LLM; when Ollama is unavailable, the response includes a graceful `llmAnalysis.status: "unavailable"` result while the deterministic dashboard analysis still completes.

The repository also contains a separate, **experimental FastAPI/LangGraph workflow** under `backend/app/`. It is useful as a development direction but is not the path started by the default command below and needs further dependency/configuration work before it should be considered production-ready. See [Experimental agent workflow](#experimental-agent-workflow) for details.

## Features

- Upload `.csv`, `.xls`, `.xlsx`, or `.xlsm` market data files.
- Recognize common OHLCV headers and NSE quote exports, including `DATE`, `OPEN`, `HIGH`, `LOW`, `CLOSE`, `LTP`, `VOLUME`, and `Total Traded Quantity`.
- Automatically remove commas and common INR prefixes from numbers, parse common Indian date formats, remove invalid rows, and sort the data chronologically.
- Require a minimum of 30 usable OHLCV rows for the dashboard analysis.
- Calculate SMA 20/50/200, EMA 20/50, RSI-14, MACD, Bollinger Bands, ATR-14, annualized volatility, support/resistance, and maximum drawdown.
- Generate a bounded technical score, trend label, weighted overall score, confidence estimate, recommendation, scenario targets, and risk notes.
- Accept optional user-supplied news/market context and send it to a local Ollama model for a second-pass qualitative view.
- Use no cloud services by default. The application runs on `127.0.0.1`.

## Architecture

```text
CSV / Excel file + optional news text
                │
                ▼
        Static browser interface
        frontend/index.html + app.js
                │ POST /api/analyze (multipart/form-data)
                ▼
      backend/server.py (local HTTP server)
                │
                ▼
          backend/analyzer.py
  ┌─────────────┼───────────────────────┐
  │             │                       │
  ▼             ▼                       ▼
File parsing  Indicators & scoring  Optional Ollama analysis
  │             │                       │
  └─────────────┴───────────────┬───────┘
                                ▼
                     JSON result rendered in UI
```

## Quick start

### Prerequisites

- Python 3.10 or newer
- `pip`
- Optional: [Ollama](https://ollama.com/) for the local LLM section of the dashboard

### Install

From the project root:

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
```

If PowerShell blocks virtual-environment activation, either allow locally created scripts according to your machine policy or invoke the virtual-environment Python directly:

```powershell
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
```

### Start the application

```powershell
python backend/server.py
```

Open [http://127.0.0.1:8000](http://127.0.0.1:8000) in a browser. Confirm the backend is healthy with:

```powershell
Invoke-RestMethod http://127.0.0.1:8000/api/health
```

Expected response:

```json
{
  "status": "ok",
  "message": "Stock Market Prediction backend is running."
}
```

### Codex bundled Python (optional)

If `python` is unavailable on `PATH` in this workspace, use:

```powershell
& 'C:\Users\Admin\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe' backend/server.py
```

## Optional local LLM analysis

The normal analysis does not require Ollama. To enable the local qualitative interpretation, install and start Ollama, then pull the configured model:

```powershell
ollama pull deepseek-r1:8b
ollama serve
```

The analyzer sends a bounded prompt to `http://127.0.0.1:11434/api/generate` using `deepseek-r1:8b`. It includes the calculated indicators, deterministic recommendation and targets, last 20 calculated OHLCV rows, and at most 5,000 characters of user-supplied news text.

The model is instructed not to invent live news or recalculate the supplied figures. Its output is supplementary interpretation, not a source of truth. If the endpoint or model is unavailable, the API still returns the deterministic result and explains why the LLM section was skipped.

## Using the dashboard

1. Enter an optional asset label, such as `RELIANCE` or `NIFTY 50`.
2. Attach a supported market-data file.
3. Optionally paste recent news, earnings notes, or market context.
4. Select **Analyze Asset**.
5. Review the current price, recommendation, confidence, indicators, projected scenarios, LLM view (if available), and risk section.

The included `sample_data.csv` and NSE-style `Quote-Equity-KAMDHENU-EQ-16-03-2026-16-06-2026_.csv` are useful test inputs.

## Input data contract

The dashboard needs these logical fields:

| Required field | Common accepted headers |
| --- | --- |
| Date | `DATE`, `Trading Date`, `timestamp`, `time` |
| Open | `OPEN`, `Open Price`, `O` |
| High | `HIGH`, `High Price`, `H` |
| Low | `LOW`, `Low Price`, `L` |
| Close | `CLOSE`, `Close Price`, `LTP`, `Last Price`, `Adj Close` |
| Volume | `VOLUME`, `VOL`, `Quantity`, `QTY`, `Total Traded Quantity` |

Column matching ignores spaces, punctuation, and capitalization. Unrelated fields are ignored, including `SERIES`, `PREV. CLOSE`, `VWAP`, `52W H`, `52W L`, `VALUE`, and trade-count columns.

Supported dates include `16-Mar-26`, `16-03-2026`, `16/03/2026`, and ISO formats such as `2026-03-16`. Values may contain commas or INR markers. Invalid/missing OHLCV rows are discarded.

For reliable results, use daily data in chronological order with at least 200 rows when possible. The app can analyze 30 rows, but SMA-50 and SMA-200 will correctly display as unavailable until enough history is present.

## Analysis workflow

### 1. File normalization

`backend/analyzer.py` detects the file type, maps available columns to canonical lowercase OHLCV fields, parses dates, cleans numeric values, drops invalid records, and sorts by date.

### 2. Technical indicators

The analyzer calculates:

- Simple moving averages: 20, 50, and 200 periods
- Exponential moving averages: 20 and 50 periods
- RSI: 14 periods
- MACD: EMA(12) − EMA(26), with a 9-period signal line
- Bollinger Bands: SMA-20 ± 2 standard deviations
- ATR: 14 periods, based on true range
- Annualized close-to-close volatility: daily-return standard deviation × √252
- Support and resistance: low/high over the latest 20 rows
- Maximum drawdown from the uploaded close series

### 3. Technical score and trend

The score is capped between `-100` and `100`. It combines moving-average position, EMA alignment, RSI condition, MACD crossover, latest close movement, and volume confirmation. The trend label is:

| Technical score | Trend |
| --- | --- |
| ≥ 35 | Bullish |
| ≤ -25 | Bearish |
| otherwise | Neutral |

### 4. Weighted dashboard score

The technical score is converted to a 0–100 scale and combined with the following weights:

| Input | Weight | Current source |
| --- | ---: | --- |
| Technical analysis | 40% | Calculated from uploaded OHLCV data |
| News | 20% | Static placeholder score |
| Indian market | 10% | Static placeholder score |
| Global market | 10% | Static placeholder score |
| Economic factors | 10% | Static placeholder score |
| Geopolitical factors | 5% | Static placeholder score |
| Election impact | 3% | Static placeholder score |
| Commodity correlation | 2% | Static placeholder score |

The contextual scores currently come from `_static_context()` in `backend/analyzer.py`; adding text in the UI does **not** automatically change those numeric weights. News text is listed in the response and supplied to Ollama if enabled.

| Overall score | Recommendation |
| --- | --- |
| > 75 | STRONG BUY |
| 60–75 | BUY |
| 45–59.99 | HOLD |
| 30–44.99 | SELL |
| < 30 | STRONG SELL |

### 5. Price scenarios and risks

Targets for 1 week, 1 month, 3 months, 6 months, and 12 months are scenario estimates based on ATR and the combined technical/overall bias. They are not trained price forecasts. The risk section includes volatility-aware best/worst estimates plus data-quality and market-event caveats.

## API reference

### `GET /api/health`

Returns server readiness.

### `POST /api/analyze`

Runs the dashboard workflow. Use `multipart/form-data`:

| Field | Required | Description |
| --- | --- | --- |
| `file` | Yes | CSV, XLS, XLSX, or XLSM OHLCV file |
| `asset` | No | Display name; an NSE quote filename is used as a fallback |
| `newsText` | No | User-provided news or market context |

Example:

```powershell
curl.exe -F "asset=KAMDHENU" -F "file=@sample_data.csv" -F "newsText=Optional market context" http://127.0.0.1:8000/api/analyze
```

Successful responses include `technicalAnalysis`, `newsAnalysis`, `finalAiScore`, `recommendation`, `priceTargets`, `risks`, and `llmAnalysis`. Client/input errors return HTTP `400` with an `error` message.

## Project layout

```text
Stock_Market_Prediction/
├── frontend/
│   ├── index.html              # Upload form and dashboard markup
│   ├── app.js                  # Form submission and response rendering
│   └── styles.css              # Dashboard styling
├── backend/
│   ├── server.py               # Default local HTTP server and API routes
│   ├── analyzer.py             # Default parsing, indicators, scoring, Ollama call
│   └── app/                    # Experimental FastAPI/LangGraph agent workflow
├── requirements.txt            # Dependencies for the default workflow
├── sample_data.csv             # Example upload file
└── README.md
```

## Experimental agent workflow

`backend/app/` is an alternate development track that exposes FastAPI routes such as `/api/upload-test`, `/api/technical-test`, and `/api/agent-test`. Its LangGraph sequence is:

```text
technical → news → risk → Random Forest prediction → XGBoost prediction → LSTM prediction → final LLM response
```

This path uses LangChain, LangGraph, scikit-learn, XGBoost, TensorFlow, and TextBlob. These packages are not all pinned in the current `requirements.txt`, and the default `backend/server.py` does not invoke this path. Treat it as a prototype until its dependencies, model validation, error handling, and tests are completed.

If you work on it, start Uvicorn from `backend/app` so its local imports resolve:

```powershell
Set-Location backend\app
uvicorn main:app --reload --host 127.0.0.1 --port 8000
```

Do not run it on the same port as `backend/server.py`.

## Development notes and limitations

- The server binds to loopback only (`127.0.0.1`) and is intended for local use.
- Uploaded files are processed in memory; no upload persistence is implemented.
- The static news, macro, geopolitical, election, and commodity inputs should be replaced with vetted live data sources before production use.
- The default app has no authentication, rate limiting, persistent storage, charting, portfolio support, backtesting, or brokerage integration.
- The LLM response may be missing, unstructured, or unavailable; deterministic calculations remain the primary output.
- Prediction horizons and confidence values are heuristic scenario outputs, not validated forecast performance metrics.

## Troubleshooting

| Problem | Likely cause and resolution |
| --- | --- |
| `Could not identify ...` | Check that the file includes all six OHLCV fields and uses a supported header alias. |
| `Please upload at least 30 rows` | Upload more valid, non-empty OHLCV records. |
| `Unsupported file type` | Use `.csv`, `.xls`, `.xlsx`, or `.xlsm`. |
| LLM status is `unavailable` | Start Ollama and run `ollama pull deepseek-r1:8b`; deterministic analysis will still work. |
| `Address already in use` | Stop the process using port 8000 or run only one backend mode at a time. |
| `ModuleNotFoundError` | Activate the correct virtual environment and reinstall with `pip install -r requirements.txt`. |

## Roadmap

- Replace static contextual scores with traceable live market, news, and macro sources.
- Add validated backtesting and train/test splits for predictive models.
- Add automated tests for parsing, indicators, scoring thresholds, and API responses.
- Consolidate the default and experimental backend paths behind a single documented API.
- Add configuration through environment variables, structured logging, and deployment hardening.

## Disclaimer

All outputs are probability-based analytical aids derived from uploaded historical data and optional local-LLM commentary. Markets are uncertain, historical patterns may fail, and the app does not account for every factor affecting a security. Make investment decisions only after independent research and, where appropriate, advice from a qualified professional.
