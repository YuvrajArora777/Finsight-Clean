import os
import logging
import pandas as pd
from openai import OpenAI

# Simulating context - in a real app, this would be passed from the UI state
def get_openai_client():
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        return None
    return OpenAI(api_key=api_key)

SYSTEM_PROMPT = """You are FinBot, an expert financial analyst assistant. 
You are embedded in a dashboard called 'FinSight'.
Your goal is to help the user understand the stock data, charts, and trends presented to them.
Always be professional, concise, and data-driven. 
If you don't know the answer, admit it. 
Do not give financial advice (e.g., 'Buy now!'). Instead say 'The trend is bullish'.
"""

def calculate_technicals(df: pd.DataFrame):
    """
    Simple 'Graph Vision' - calculates support, resistance, and trend.
    """
    if df.empty: return "No data available."
    
    last_close = df["Close"].iloc[-1]
    max_price = df["High"].max()
    min_price = df["Low"].min()
    
    # Simple Trend (Price vs 20-day MA)
    ma_20 = df["Close"].rolling(20).mean().iloc[-1] if len(df) >= 20 else last_close
    trend = "BULLISH" if last_close > ma_20 else "BEARISH"
    
    return f"""
    - Current Price: ${last_close:.2f}
    - 60-Day High (Resistance): ${max_price:.2f}
    - 60-Day Low (Support): ${min_price:.2f}
    - Technical Trend: {trend} (Price vs 20-MA)
    """

def generate_chat_response(messages, current_ticker, recent_data: pd.DataFrame, prediction=None, market_context=None, sentiment_context=None):
    """
    Generate a response from OpenAI with context about the current stock.
    Enhanced with Sentiment and Technicals.
    """
    client = get_openai_client()
    if not client:
        return "Broadcasting from FinBot: I'm offline! (Missing OpenAI Key)"

    # Create Context Block
    context = f"User is currently looking at {current_ticker}.\n"
    
    if not recent_data.empty:
        # 1. Technical 'Graph Vision'
        technicals = calculate_technicals(recent_data)
        context += f"\nTECHNICAL ANALYSIS (Visual Trends):\n{technicals}\n"
        
        # Data Dump (Still useful for specific numbers)
        context += f"\nLatest Data (Last 5 Days):\n{recent_data.tail(5).to_string()}\n"
    
    if prediction:
        context += f"\nAI PREDICTION (LSTM Model):\nTomorrow's Price: ${prediction['price']:.2f} ({prediction['direction']})\n"
    
    if sentiment_context:
        # 2. News/Sentiment Context
        context += f"\nNEWS SENTIMENT (Latest Headlines):\n"
        for item in sentiment_context[:3]: # Top 3
            context += f"- [{item['sentiment_label']}] {item['title']} (Score: {item['sentiment_score']:.2f})\n"

    if market_context:
        context += f"\nMARKET CONTEXT (Comparisons):\n{market_context}\n"
    
    full_messages = [{"role": "system", "content": SYSTEM_PROMPT + f"\n\nCONTEXT:\n{context}"}]
    full_messages.extend(messages)

    try:
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=full_messages,
            max_tokens=400
        )
        return response.choices[0].message.content
    except Exception as e:
        return f"FinBot Error: {str(e)}"
