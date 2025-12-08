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

def generate_chat_response(messages, current_ticker, recent_data: pd.DataFrame, prediction=None, market_context=None):
    """
    Generate a response from OpenAI with context about the current stock.
    messages: List of {"role": "user", "content": "..."} dicts.
    current_ticker: "AAPL"
    recent_data: DataFrame of last 5 days
    prediction: Optional dict {"price": 123.45, "direction": "UP/DOWN"}
    market_context: Optional str (summary of other stocks)
    """
    client = get_openai_client()
    if not client:
        return "Broadcasting from FinBot: I'm offline! (Missing OpenAI Key)"

    # Create Context Block
    context = f"User is currently looking at {current_ticker}.\n"
    if not recent_data.empty:
        last_close = recent_data.iloc[-1]['Close']
        prev_close = recent_data.iloc[-2]['Close'] if len(recent_data) > 1 else last_close
        change = ((last_close - prev_close) / prev_close) * 100
        
        context += f"Latest Data (Last 5 Days):\n{recent_data.tail(5).to_string()}\n"
        context += f"Current Price: ${last_close:.2f} (Change: {change:.2f}%)\n"
    
    if prediction:
        context += f"AI Prediction for Tomorrow: ${prediction['price']:.2f} ({prediction['direction']})\n"
    
    if market_context:
        context += f"\nMARKET CONTEXT (Use for comparisons):\n{market_context}\n"
    
    # Prepend context to the last user message to "inject" it invisibly to the LLM
    # (Or add as a system message update). 
    # Here we'll add it as a system instruction for this turn.
    
    full_messages = [{"role": "system", "content": SYSTEM_PROMPT + f"\n\nCONTEXT:\n{context}"}]
    full_messages.extend(messages)

    try:
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=full_messages,
            max_tokens=300
        )
        return response.choices[0].message.content
    except Exception as e:
        return f"FinBot Error: {str(e)}"
