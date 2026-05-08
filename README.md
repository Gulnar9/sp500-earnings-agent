# S&P 500 Earnings Intelligence Agent

> **Disclaimer:** This project is for educational and research purposes only. It does not constitute financial advice. Past earnings patterns do not guarantee future results. Always consult a qualified financial advisor before making investment decisions.

---

## Overview

A LangGraph-powered financial research agent that automatically generates structured pre-earnings briefings for S&P 500 stocks. The agent fetches earnings history, calendar and news sentiment for a given ticker. Calculates quantitative signals based on volatility, cosistency and produces structured reports. The purpose is to observe patterns not to make buy or sell recommendations.

Built as a part of my portfolio demonstrating agentic AI workflows, financial data engineering and LLM-powered report generation.

---

## Agent Workflow

```
START
  │
  ▼
fetch_data          ← earnings history, price data, company overview, news
  │
  ▼
analysis_node       ← beat streak, consistency score, drift, volatility ratio, signal
  │
  ▼
signal_router       ← conditional edge: STRONG / NEUTRAL / WEAK
  │
  ▼
generate_report     ← LLM produces structured pre-earnings briefing
  │
  ▼
END
```

### Nodes

| Node | Responsibility |
|---|---|
| `fetch_data` | Fetches raw data from Alpha Vantage API with local disk caching |
| `analysis_node` | Computes quantitative metrics and assigns signal strength |
| `signal_router` | Conditional edge — routes based on signal score |
| `generate_report` | Calls GPT-4o with system prompt + state data to generate briefing |

---

## Quantitative Metrics

| Metric | Description | Weight in Signal Score |
|---|---|---|
| Beat streak | Consecutive quarters beating EPS estimates | 35% |
| Consistency score | Mean / std of surprise percentages | 35% |
| Pre-earnings volatility | Recent 10-day vol vs normal vol ratio | 15% |
| Price drift | 5-day directional price movement before earnings | 15% |

**Signal thresholds:**
- `STRONG` → score > 0.70
- `NEUTRAL` → score 0.40 – 0.70
- `WEAK` → score < 0.40

---

## Report Output Format

Each briefing includes:

- Quarterly EPS table (last 8 quarters): reported date, fiscal date, actual EPS, estimated EPS, surprise, surprise %
- Signal strength classification
- Pattern summary — historical beat/miss behavior
- Price behavior — pre-earnings drift and volatility analysis
- Key risk factors
- News sentiment summary
- What to watch — single most important metric for the upcoming report

---

## Tech Stack

| Component | Technology |
|---|---|
| Agent orchestration | LangGraph |
| LLM | GPT-4o via LangChain OpenAI |
| Financial data | Alpha Vantage API |
| Data processing | pandas, numpy |
| Caching | Local disk (JSON) |
| Environment | python-dotenv |

---

## Project Structure

```
agents/
├── src/
│   └── fin_agent.py       ← main agent script
├── cache/                 ← auto-generated API response cache (gitignored)
├── .env                   ← API keys (gitignored)
├── .gitignore
├── requirements.txt
└── README.md
```

---

## Setup

### Prerequisites

- Python 3.11 
- OpenAI API key
- Alpha Vantage API key

### Installation

```bash
# Clone the repository
git clone https://github.com/yourusername/sp500-earnings-agent.git
cd sp500-earnings-agent

# Create and activate virtual environment
python -m venv venv
venv\Scripts\activate        # Windows
source venv/bin/activate     # Mac/Linux

# Install dependencies
pip install -r requirements.txt
```

### Environment Variables

Create a `.env` file in the project root:

```
OPENAI_API_KEY=sk-...
ALPHA_API_KEY=your_alpha_vantage_key
```

Register for a free Alpha Vantage key at [alphavantage.co](https://www.alphavantage.co/support/#api-key).

### Run

```bash
cd src
python fin_agent.py
```

---

## API Rate Limits

Alpha Vantage free tier allows **25 requests per day**. The agent uses local disk caching to avoid redundant API calls during development — cached responses are stored in `cache/` and reused on subsequent runs.

To clear the cache and fetch fresh data:

```bash
# Windows
Remove-Item -Recurse -Force cache

# Mac/Linux
rm -rf cache/
```

---

## Example Output

```
**Company:** Apple Inc. (AAPL)

**Quarterly Report:**
| reportDate | fiscalDate | epsActual | epsEstimate | surprise | surprisePercent |
|---|---|---|---|---|---|
| 2026-01-30 | 2025-12-31 | 2.40 | 2.35 | 0.05 | 2.13% |
| ...        | ...        | ...  | ...  | ...  | ...   |

**Earnings Date:** 2026-04-30
**Signal:** STRONG

**Pattern Summary**
Apple has beaten EPS estimates in 7 of the last 8 quarters...

**Price Behavior**
Pre-earnings drift of +2.3% over the last 5 trading days suggests...

**Key Risk Factors**
- Slowing iPhone upgrade cycle in mature markets
- Exposure to US-China trade policy uncertainty

**News Sentiment**
Recent coverage is broadly positive, with analyst commentary focused on services revenue growth...

**What to Watch**
Monitor services revenue growth guidance — this has been the primary driver of post-earnings price reaction in recent quarters.
```

---

## Limitations

- Free Alpha Vantage tier limits per day
- Signal score weights are assumption-based, not derived from historical behaviour
- Pre-earnings drift uses the last reported earnings date, not the upcoming one
- News sentiment is passed as raw feed data — no dedicated NLP scoring model


