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

## Example Output

```
================================== Ai Message ==================================

**Company:** Apple Inc. (AAPL)  
**Quarterly report:**  

| Report Date | Fiscal Date | EPS Actual | EPS Estimate | Surprise | Surprise % |
|-------------|-------------|------------|--------------|----------|------------|
| 2026-04-30  | 2026-03-31  | 2.01       | 1.94         | 0.07     | 3.6082     |
| 2026-01-29  | 2025-12-31  | 2.84       | 2.67         | 0.17     | 6.367      |
| 2025-10-30  | 2025-09-30  | 1.85       | 1.77         | 0.08     | 4.5198     |
| 2025-07-31  | 2025-06-30  | 1.57       | 1.43         | 0.14     | 9.7902     |
| 2025-05-01  | 2025-03-31  | 1.65       | 1.62         | 0.03     | 1.8519     |
| 2025-01-30  | 2024-12-31  | 2.4        | 2.34         | 0.06     | 2.5641     |
| 2024-10-31  | 2024-09-30  | 0.97       | 0.95         | 0.02     | 2.1053     |
| 2024-08-01  | 2024-06-30  | 1.4        | 1.34         | 0.06     | 4.4776     |

**Earnings Date:** 2026-04-30  
**Signal:** STRONG

**Pattern Summary**  
Apple Inc. has demonstrated a consistent ability to surpass earnings expectations over the past eight quarters, maintaining a consecutive beat streak. The average earnings surprise for these periods reflects a commendable capacity to outpace analyst estimates, contributing to a high surprise consistency score of 1.788. This robust performance indicates a strong handle on forecast alignment and execution.

**Price Behavior**  
In the 10 days prior to earnings, Apple has experienced a 1.207% price drift, indicating a marginal positive shift in investor sentiment leading up to results. Interestingly, volatility is slightly higher pre-earnings at 1.208%, suggesting heightened investor activity and anticipation ahead of the earnings report. Last quarter’s EPS beat of $0.07 above the consensus was a continuation of this trend, reinforcing positive investor sentiment.

**Key Risk Factors**
- Potential regulatory challenges impacting revenue streams or operational efficiency.
- Market saturation in key segments such as smartphones and personal computing devices.


**News Sentiment**
Recent sentiment around Apple's market performance remains generally neutral with articles discussing broader market movements and institutional reactions in related firms, rather than direct focus on Apple itself.

**What to Watch**
Keep an eye on Apple's Services revenue growth rate, as it serves as a critical indicator of the company's ability to expand its ecosystem beyond hardware sales.

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
## Guardrails 

- Signal score weights are assumption-based, not derived from historical behaviour
- Currently pre-earnings drift uses the last reported earnings date, not the upcoming one


