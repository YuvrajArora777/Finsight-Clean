import os
import logging
import pandas as pd
import numpy as np
from io import StringIO
from azure.storage.blob import BlobServiceClient

# Configure logging
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")

def get_openai_client():
    """Lazy load OpenAI client to avoid errors if not installed/configured."""
    try:
        from openai import OpenAI
        api_key = os.getenv("OPENAI_API_KEY")
        if not api_key:
            return None
        return OpenAI(api_key=api_key)
    except ImportError:
        logging.warning("OpenAI library not installed. Using local fallback.")
        return None

def generate_local_insight(df: pd.DataFrame, ticker: str) -> str:
    """Generate a template-based insight using pandas stats (Fallback)."""
    if df.empty:
        return f"{ticker}: No data available for insight."
    
    # Calculate stats
    latest_close = df["Close"].iloc[-1]
    prev_close = df["Close"].iloc[-2] if len(df) > 1 else latest_close
    daily_return = ((latest_close - prev_close) / prev_close) * 100
    
    volatility = df["return_pct"].std() * 100
    avg_volume = df["Volume"].mean()
    
    trend = "bullish" if daily_return > 0 else "bearish"
    vol_desc = "high" if volatility > 2.0 else "stable"
    
    insight = (
        f"{ticker} closed at ${latest_close:.2f}, showing a {trend} move of {daily_return:.2f}%. "
        f"Volatility remains {vol_desc} ({volatility:.2f}%), with an average volume of {int(avg_volume):,} shares. "
        f"Market sentiment appears {trend} based on recent price action."
    )
    return insight

def generate_openai_insight(client, df: pd.DataFrame, ticker: str) -> str:
    """Generate a natural language insight using OpenAI GPT-4o-mini."""
    if df.empty:
        return f"{ticker}: No data available."
    
    # Summarize last 5 days as context
    recent_data = df.tail(5).to_string()
    
    prompt = (
        f"Analyze the following recent stock data for {ticker}:\n\n{recent_data}\n\n"
        "Provide a concise, 1-sentence financial insight suitable for a dashboard. "
        "Focus on trend, volatility, and volume. Do not use markdown."
    )
    
    try:
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": "You are a financial analyst bot."},
                {"role": "user", "content": prompt}
            ],
            max_tokens=60
        )
        return response.choices[0].message.content.strip()
    except Exception as e:
        logging.error(f"OpenAI generation failed for {ticker}: {e}")
        return generate_local_insight(df, ticker)

def run_ai_pipeline(blob_service_client: BlobServiceClient, processed_container: str):
    """Main function to generate insights for all tickers and upload to Azure."""
    logging.info("Starting AI Insight Generation...")
    
    # Check for OpenAI Key
    client = get_openai_client()
    mode = "OpenAI" if client else "Local Fallback"
    logging.info(f"AI Mode: {mode}")

    tickers_str = os.getenv("STOCK_TICKERS", "AAPL,MSFT,TSLA,GOOGL,AMZN")
    tickers = [t.strip() for t in tickers_str.split(",") if t.strip()]
    
    insights = []

    for ticker in tickers:
        try:
            # Download processed data from Azure (or use local if integrated, but let's fetch to be safe/stateless)
            blob_name = f"{ticker}_processed.csv"
            blob_client = blob_service_client.get_blob_client(container=processed_container, blob=blob_name)
            
            if not blob_client.exists():
                logging.warning(f"Blob {blob_name} not found. Skipping.")
                continue

            download_stream = blob_client.download_blob()
            df = pd.read_csv(StringIO(download_stream.content_as_text()), index_col=0)
            
            if client:
                insight_text = generate_openai_insight(client, df, ticker)
            else:
                insight_text = generate_local_insight(df, ticker)
            
            insights.append({"Ticker": ticker, "Insight": insight_text, "Date": pd.Timestamp.now().strftime("%Y-%m-%d")})
            logging.info(f"Generated insight for {ticker}")
            
        except Exception as e:
            logging.error(f"Error processing insights for {ticker}: {e}")

    # Save to CSV
    if insights:
        insights_df = pd.DataFrame(insights)
        output = StringIO()
        insights_df.to_csv(output, index=False)
        
        # Upload insights.csv
        target_blob_client = blob_service_client.get_blob_client(container=processed_container, blob="ai_insights.csv")
        target_blob_client.upload_blob(output.getvalue().encode("utf-8"), overwrite=True)
        logging.info("Successfully uploaded ai_insights.csv to Azure.")
    else:
        logging.warning("No insights generated.")

if __name__ == "__main__":
    # Local Test
    from dotenv import load_dotenv
    load_dotenv()
    # Mocking client for local test would require real connection string, skipping auto-run
    print("Run via main.py or ensure env vars are set.")
