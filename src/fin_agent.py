import os
import requests
import json
import time
import numpy as np
import pandas as pd
from pathlib import Path
from dotenv import load_dotenv
from langgraph.graph import StateGraph, START, END
from langchain_openai import ChatOpenAI
from typing import Annotated, Sequence, TypedDict
from langchain_core.messages import BaseMessage, AIMessage, SystemMessage
from langgraph.graph.message import add_messages
from langgraph.graph import StateGraph, END
from IPython.display import Image, display


BASE_DIR = Path(__file__).resolve().parent.parent
load_dotenv(BASE_DIR / ".env")

OPENAI_API_KEY = os.environ["OPENAI_API_KEY"]
ALPHA_API_KEY = os.environ["ALPHA_API_KEY"]

class AgentState(TypedDict):
    messages: Annotated[Sequence[BaseMessage], add_messages] 
    ticker: str 
    reportDate: str
    fiscalDate: str
    earnings_date: str
    epsActual: float
    epsEstimate: float
    surprise: float
    surprisePercent: float
    daily_rates: list
    overview: list
    news_sentiment: list
    signal: str
    pre_earnings_vol: float
    beat_streak: int
    consistency: float
    drift: float


# api request to fetch the stock data 
def alpha(function: str, ticker: str) -> dict:
    """Fetch ticker data"""
    response = requests.get(
        "https://www.alphavantage.co/query",
        params={"function": function, "symbol": ticker, "apikey": ALPHA_API_KEY},
        timeout=60
    )
    return response.json()


# cache data to avoid api limitations
def alpha_cached(function: str, ticker: str) -> dict:
    """Fetches from Alpha Vantage, caches to disk to save API calls."""
    cache_path = Path(f"cache/{ticker}_{function}.json")
    cache_path.parent.mkdir(exist_ok=True)

    if cache_path.exists():
        return json.loads(cache_path.read_text())

    time.sleep(1) 
    data = alpha(function, ticker)
    cache_path.write_text(json.dumps(data))
    return data


def get_stock_data(state: AgentState) -> AgentState:
    """Fetches earnings calendar and history for a given ticker."""
    ticker = state["ticker"]

    earnings  = alpha_cached("EARNINGS", ticker)["quarterlyEarnings"][:8]
    time.sleep(2)  # wait 2 seconds between api calls

    daily_rates = alpha_cached("TIME_SERIES_DAILY", ticker)
    time.sleep(2)

    overview  = alpha_cached("OVERVIEW", ticker)
    time.sleep(2)

    news = alpha_cached("NEWS_SENTIMENT", ticker)["feed"][:5]

    state["reportDate"] = [e['reportedDate'] for e in earnings]
    state["fiscalDate"] = [e['fiscalDateEnding'] for e in earnings]
    state["epsActual"] = [e['reportedEPS'] for e in earnings]
    state["epsEstimate"] = [e['estimatedEPS'] for e in earnings]
    state["surprise"] = [e['surprise'] for e in earnings]
    state["surprisePercent"] = [e['surprisePercentage'] for e in earnings]
    state["daily_rates"] = daily_rates.get("Time Series (Daily)")
    state["overview"] = overview
    state["news_sentiment"] = news

    return state


def calc_pre_earnings_vol(reportDate: list, rates) -> float:
    """Calculates 10 days volatility prior to earnings statement."""
    
    # get last earnings report date
    lastReportDate = reportDate[0]

    # get time series of last 30 days prior to last earnings report date
    df = pd.DataFrame(rates).T
    df = df[df.index < lastReportDate]
    df["close"] = df["4. close"].astype(float)
    last_30_days = df.head(30)

    # calculate drift in close value prior to earnings
    pre_earnings_vol = last_30_days["close"].pct_change().head(10).std()
    normal_vol = last_30_days["close"].pct_change().std()
    pre_earnings_drift = round(pre_earnings_vol / normal_vol, 3)

    return pre_earnings_drift


def calc_consistency(surprise_perc: list) -> float:
    """Calculate consistency of beat"""
    surprises = np.array([float(s) for s in surprise_perc])
    if len(surprises) < 2:
        return 0.0
    mean_surprise = surprises.mean()      
    std_surprise = surprises.std()        
    consistency = round(mean_surprise / std_surprise, 3) if std_surprise != 0 else 0.0

    return consistency


def calc_streak(surprise_perc: list) -> int:
    """Calculates consecutive quarters beating estimates."""
    streak = 0
    for s in surprise_perc:
        if float(s) > 0:
            streak += 1
        else:
            break
        
    return streak


def calc_drift(reportDate: list, rates) -> float:
    """Calculates 5 days drift prior to earnings statement."""
    
    # get last earnings report date
    lastReportDate = reportDate[0]

    # get time series of last 5 days prior to last earnings report date
    df = pd.DataFrame(rates).T
    df.index = pd.to_datetime(df.index)
    df = df[df.index < lastReportDate]
    df["close"] = df["4. close"].astype(float)
    last_5 = df.head(5)

    if len(last_5) < 2:
        return 0.0

    price_start = last_5["close"].iloc[0]  
    price_end   = last_5["close"].iloc[-1]  

    drift = (price_end - price_start) / price_start * 100
    return round(drift, 3)



def analysis_node(state: AgentState) -> AgentState:
    norm_streak = min(calc_streak(state["surprisePercent"])/8, 1.0)
    norm_drift = min(max((calc_drift(state["reportDate"], state["daily_rates"]) + 5)/ 10, 0), 1.0)
    norm_vol = max(0, 1 - (calc_pre_earnings_vol(state["reportDate"], state["daily_rates"]) - 1) / 1.0)
    norm_consistency = min(max(calc_consistency(state["surprisePercent"]), 0), 1.0)

    signal_score = (
        norm_streak * 0.35 +
        norm_consistency * 0.35 +
        norm_vol  * 0.15 +
        norm_drift * 0.15
        )
    
    if signal_score > 0.7:
        state["signal"] = "STRONG"
    elif signal_score > 0.4:
        state["signal"] = "NEUTRAL"
    else:
        state["signal"] = "WEAK"

    state["beat_streak"] = calc_streak(state["surprisePercent"])
    state["consistency"] = calc_consistency(state["surprisePercent"])
    state["drift"] = calc_drift(state["reportDate"], state["daily_rates"])
    state["pre_earnings_vol"] = calc_pre_earnings_vol(state["reportDate"], state["daily_rates"])
    state["earnings_date"] = state["reportDate"][0]
    
    return state


def signal_router(state: AgentState) -> AgentState:
    """Given consistency, streak and pre_earnings_drift, create flag on strength of pattern"""

    if state["signal"] == "STRONG":
        return "strong_signal"
    
    elif state["signal"] == "NEUTRAL":
        return "neutral_signal"
    
    else:
        return "weak_signal"
             

model = ChatOpenAI(model = "gpt-4o")


def model_call(state:AgentState) -> AgentState:
    system_prompt = SystemMessage(content=
        """
        You are a financial research assistant specializing in S&P 500 earnings analysis.

        ## Role
        Generate structured pre-earnings briefings for given ticker based on quantitative data provided.
        Do not predict stock prices or give investment advice!

        ## Input Data You Will Receive
        - Ticker and company overview
        - Last earnings date
        - Analyst consensus EPS estimate
        - Historical earnings surprises (last 8 quarters)
        - Pre-earnings price drift (10 days)
        - Consecutive beat streak
        - Surprise consistency score
        - Signal strength: strong / neutral / weak

        ## Output Format
        Always respond in this exact structure:


        **Company:** {name} ({ticker})  
        **Quarterly report:** {reportDate}, {fiscalDate}, {epsActual}, {epsEstimate}, {surprise}, {surprisePercent}
        Show last 8 quarters only, display column names as headers. Do not change date format.

        **Earnings Date:** {earnings_date}  
        **Signal:** {STRONG | NEUTRAL | WEAK}

        **Pattern Summary**
        2-3 sentences on historical beat/miss behavior and consistency.

        **Price Behavior**
        2-3 insights on pre-earnings drift and volatility vs normal periods, highlight last quarter EPS results.


        **Key Risk Factors**
        Bullet 1
        Bullet 2
        
        **News Sentiment**
        1-2 sentences of latest news sentiment.


        **What to Watch**
        One sentence on the single most important metric to monitor when results drop.

        ## Strict Rules
        - Never say buy, sell, or recommend any position
        - Never speculate beyond the data provided
        - If data is missing for a field, state "insufficient data" for that section
        - Keep each report under 800 words
        - Maintain consistent tone 
        """
    )
    
     # build data context from state
    data_message = SystemMessage(content=f"""
    Current data for {state['ticker']}:
    - Report Dates: {state['reportDate']}
    - Fiscal Dates: {state['fiscalDate']}
    - EPS Actual: {state['epsActual']}
    - EPS Estimate: {state['epsEstimate']}
    - Surprise %: {state['surprisePercent']}
    - Earnings Date: {state['earnings_date']}
    - Beat Streak: {state['beat_streak']}
    - Drift: {state['drift']}
    - Consistency Score: {state['consistency']}
    - Pre-earnings Volatility: {state['pre_earnings_vol']}
    - Signal: {state['signal']}
    - News Sentiment: {state['news_sentiment']}

        """)
    response = model.invoke([system_prompt, data_message] + state["messages"])
    return {"messages": [response]}


graph = StateGraph(AgentState)

graph.add_node("fetch_data", get_stock_data)
graph.add_node("analysis_node", analysis_node)
graph.add_node("generate_report", model_call)

graph.add_edge(START,"fetch_data")
graph.add_edge("fetch_data", "analysis_node")
graph.add_conditional_edges("analysis_node", 
                            signal_router,
                            {   "strong_signal": "generate_report",
                                "neutral_signal": "generate_report",
                                "weak_signal": "generate_report",
                             }
                            )
graph.add_edge("generate_report", END)

app = graph.compile()


def print_stream(stream):
    for s in stream:
        message = s["messages"][-1]
        if isinstance(message, AIMessage):
            message.pretty_print()

inputs = {
    "ticker": "AAPL",
    "messages": [("user", "Provide pre-earnings briefing for AAPL")]
        }

print_stream(app.stream(inputs, stream_mode="values"))

#display(Image(app.get_graph().draw_mermaid_png()))


