const form = document.querySelector("#analysisForm");
const fileInput = document.querySelector("#fileInput");
const fileName = document.querySelector("#fileName");
const submitButton = document.querySelector("#submitButton");
const emptyState = document.querySelector("#emptyState");
const loadingState = document.querySelector("#loadingState");
const errorState = document.querySelector("#errorState");
const results = document.querySelector("#results");

fileInput.addEventListener("change", () => {
  fileName.textContent = fileInput.files[0]?.name || "Attach CSV / Excel file";
});

form.addEventListener("submit", async (event) => {
  event.preventDefault();
  const data = new FormData(form);

  if (!fileInput.files.length) {
    showError("Please attach a CSV or Excel file first.");
    return;
  }

  setLoading(true);
  try {
    const response = await fetch("/api/analyze", {
      method: "POST",
      body: data,
    });
    const payload = await response.json();
    if (!response.ok) {
      throw new Error(payload.error || "Analysis failed.");
    }
    renderResults(payload);
  } catch (error) {
    showError(error.message);
  } finally {
    setLoading(false);
  }
});

function setLoading(isLoading) {
  submitButton.disabled = isLoading;
  submitButton.textContent = isLoading ? "Analyzing..." : "Analyze Asset";
  loadingState.classList.toggle("hidden", !isLoading);
  if (isLoading) {
    emptyState.classList.add("hidden");
    errorState.classList.add("hidden");
    results.classList.add("hidden");
  }
}

function showError(message) {
  emptyState.classList.add("hidden");
  loadingState.classList.add("hidden");
  results.classList.add("hidden");
  errorState.classList.remove("hidden");
  errorState.textContent = message;
}

function renderResults(data) {
  emptyState.classList.add("hidden");
  errorState.classList.add("hidden");
  results.classList.remove("hidden");

  text("#assetName", data.asset);
  text("#dateRange", `${data.dateRange.from} to ${data.dateRange.to} | ${data.rowsAnalyzed} rows analyzed`);
  text("#currentPrice", formatMoney(data.currentPrice));
  text("#recommendation", data.recommendation);
  setRecommendationClass(data.recommendation);

  text("#overallScore", data.finalAiScore.overallScore);
  text("#confidence", `${data.finalAiScore.confidence}% confidence`);
  text("#technicalScore", data.technicalAnalysis.score);
  text("#trend", data.trend);
  text("#newsScore", data.newsAnalysis.score);
  text("#newsLabel", data.newsAnalysis.classification);
  text("#indianScore", data.marketSentiment.indianScore);
  text("#indianLabel", data.marketSentiment.indianLabel);
  text("#globalScore", data.marketSentiment.globalScore);
  text("#globalLabel", data.marketSentiment.globalLabel);
  text("#economicScore", data.economicAnalysis.score);
  text("#economicLabel", data.economicAnalysis.label);
  renderLlmAnalysis(data.llmAnalysis);

  text("#support", formatMoney(data.technicalAnalysis.support));
  text("#resistance", formatMoney(data.technicalAnalysis.resistance));
  text("#rsi", safeValue(data.technicalAnalysis.rsi));
  text("#macd", safeValue(data.technicalAnalysis.macd));
  text("#atr", formatMoney(data.technicalAnalysis.atr));
  text("#volatility", `${data.technicalAnalysis.volatility}%`);
  text("#drawdown", `${data.technicalAnalysis.drawdown}%`);
  text("#sma200", safeMoney(data.technicalAnalysis.sma200));

  renderList("#signals", data.technicalAnalysis.signals);
  renderTargets(data.priceTargets);
  text("#worstCase", formatMoney(data.risks.worstCaseEstimate));
  text("#bestCase", formatMoney(data.risks.bestCaseEstimate));
  renderList("#risks", [...data.risks.keyRisks, ...data.risks.downsideScenarios]);
  text("#explanation", data.explanation);
  text("#disclaimer", data.disclaimer);
}

function renderLlmAnalysis(analysis) {
  if (!analysis) {
    text("#llmModel", "deepseek-r1:8b");
    text("#llmStatus", "not returned");
    text("#llmRecommendation", "-");
    text("#llmSummary", "No local LLM analysis was returned by the backend.");
    renderList("#llmReasoning", []);
    return;
  }

  text("#llmModel", analysis.model || "deepseek-r1:8b");
  text("#llmStatus", analysis.status || "ok");
  text("#llmRecommendation", analysis.recommendation || "-");
  text("#llmSummary", analysis.summary || analysis.newsImpact || "Local model returned analysis without a summary.");

  const reasoning = Array.isArray(analysis.reasoning) ? analysis.reasoning : [];
  const risks = Array.isArray(analysis.riskNotes) ? analysis.riskNotes : [];
  renderList("#llmReasoning", [...reasoning, ...risks].slice(0, 8));
}

function setRecommendationClass(value) {
  const node = document.querySelector("#recommendation");
  node.className = "recommendation";
  node.classList.add(value.toLowerCase().replaceAll(" ", "-"));
}

function renderTargets(targets) {
  const labels = {
    "1Week": "1 Week",
    "1Month": "1 Month",
    "3Month": "3 Month",
    "6Month": "6 Month",
    "12Month": "12 Month",
  };
  const container = document.querySelector("#targets");
  container.innerHTML = Object.entries(targets)
    .map(([key, target]) => {
      return `
        <div class="target-row">
          <strong>${labels[key]}</strong>
          <span>
            ${formatMoney(target.targetPrice)}
            <small>${target.probability}% probability | ${target.confidence}% confidence</small>
          </span>
        </div>
      `;
    })
    .join("");
}

function renderList(selector, items) {
  const node = document.querySelector(selector);
  node.innerHTML = items.map((item) => `<li>${escapeHtml(item)}</li>`).join("");
}

function text(selector, value) {
  document.querySelector(selector).textContent = value;
}

function safeValue(value) {
  return value === null || value === undefined ? "Not enough data" : value;
}

function safeMoney(value) {
  return value === null || value === undefined ? "Not enough data" : formatMoney(value);
}

function formatMoney(value) {
  return new Intl.NumberFormat("en-IN", {
    style: "currency",
    currency: "INR",
    maximumFractionDigits: 2,
  }).format(value);
}

function escapeHtml(value) {
  return String(value)
    .replaceAll("&", "&amp;")
    .replaceAll("<", "&lt;")
    .replaceAll(">", "&gt;")
    .replaceAll('"', "&quot;")
    .replaceAll("'", "&#039;");
}
