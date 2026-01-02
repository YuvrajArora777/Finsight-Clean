import yfinance as yf
import pandas as pd
import logging
from textblob import TextBlob
from datetime import datetime

def fetch_and_analyze_news(ticker: str, limit=5):
    """
    Fetches latest news for a ticker and calculates sentiment.
    Returns a list of dictionaries with title, link, and sentiment score.
    """
    try:
        stock = yf.Ticker(ticker)
        news_items = stock.news
        
        results = []
        
        for item in news_items[:limit]:
            # Extract fields based on the raw structure we observed
            content = item.get('content', {})
            title = content.get('title')
            
            # Try to find URL suitable for clicking
            link_obj = content.get('clickThroughUrl')
            link = link_obj.get('url') if link_obj else None
            
            if not title:
                continue
                
            # Calculate Sentiment
            # Polarity: -1.0 (Negative) to 1.0 (Positive)
            blob = TextBlob(title)
            sentiment_score = blob.sentiment.polarity
            
            # Subjectivity: 0.0 (Objective) to 1.0 (Subjective)
            subjectivity = blob.sentiment.subjectivity
            
            results.append({
                "ticker": ticker,
                "title": title,
                "link": link,
                "sentiment_score": sentiment_score,
                "sentiment_label": "POSITIVE" if sentiment_score > 0.1 else "NEGATIVE" if sentiment_score < -0.1 else "NEUTRAL",
                "subjectivity": subjectivity,
                "fetched_at": datetime.utcnow().isoformat()
            })
            
        return results

    except Exception as e:
        logging.error(f"Error fetching news for {ticker}: {e}")
        return []

import os
from io import StringIO
from azure.storage.blob import BlobServiceClient

def run_sentiment_pipeline(blob_service_client: BlobServiceClient, processed_container: str):
    """
    Main function to fetch news sentiment for all tickers and upload to Azure.
    """
    logging.info("Starting News Sentiment Analysis Pipeline...")
    
    tickers_str = os.getenv("STOCK_TICKERS", "AAPL,MSFT,TSLA,GOOGL,AMZN")
    tickers = [t.strip() for t in tickers_str.split(",") if t.strip()]
    
    all_news = []
    
    for ticker in tickers:
        try:
            news_items = fetch_and_analyze_news(ticker)
            if news_items:
                all_news.extend(news_items)
                logging.info(f"Fetched {len(news_items)} news items for {ticker}")
            else:
                logging.warning(f"No news found for {ticker}")
        except Exception as e:
            logging.error(f"Error in sentiment pipeline for {ticker}: {e}")
            
    if all_news:
        df = pd.DataFrame(all_news)
        
        # Save to CSV in memory
        output = StringIO()
        df.to_csv(output, index=False)
        
        # Upload to Azure
        try:
            blob_client = blob_service_client.get_blob_client(container=processed_container, blob="sentiment_analysis.csv")
            blob_client.upload_blob(output.getvalue().encode("utf-8"), overwrite=True)
            logging.info("Successfully uploaded sentiment_analysis.csv to Azure.")
        except Exception as e:
            logging.error(f"Failed to upload sentiment CSV: {e}")
    else:
        logging.warning("No news data collected for any ticker.")

if __name__ == "__main__":
    # Local Test
    print("--- Testing Sentiment Engine ---")
    data = fetch_and_analyze_news("AAPL")
    for row in data:
        print(f"[{row['sentiment_label']}] {row['sentiment_score']:.2f} | {row['title']}")
