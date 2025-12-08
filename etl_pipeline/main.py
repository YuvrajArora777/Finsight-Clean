import yfinance as yf
import requests
import pandas as pd
from azure.storage.blob import BlobServiceClient
import os
from dotenv import load_dotenv
import io
import logging
import time
from . import ai_insights
from . import lstm_predictor

# Configure logging once at module level
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")

ALPHA_VANTAGE_URL = "https://www.alphavantage.co/query"

def fetch_stock_data(ticker: str) -> pd.DataFrame:
    """Fetch daily stock data for a given ticker from Yahoo Finance."""
    logging.info(f"Fetching data for {ticker} from Yahoo Finance...")
    
    # Download data with auto_adjust=True to get split/dividend adjusted prices
    try:
        df = yf.download(ticker, period="5y", interval="1d", auto_adjust=True, progress=False)
        
        if df.empty:
            logging.warning(f"No data found for {ticker}")
            return pd.DataFrame()

        # Ensure we have standard columns
        # yfinance columns: Open, High, Low, Close, Volume
        # If multi-level columns (Ticker), drop the level
        if isinstance(df.columns, pd.MultiIndex):
            df.columns = df.columns.droplevel(1)
            
        # Select and order columns matches existing pipeline expectations
        required_cols = ["Open", "High", "Low", "Close", "Volume"]
        # Filter for existing columns only just in case
        available_cols = [c for c in required_cols if c in df.columns]
        df = df[available_cols]
        
        return df

    except Exception as e:
        logging.error(f"Error fetching {ticker} from yfinance: {e}")
        return pd.DataFrame()


def upload_to_azure(blob_service_client: BlobServiceClient, container: str, blob_name: str, df: pd.DataFrame, include_index=False):
    """Upload a DataFrame to Azure Blob Storage."""
    output = io.StringIO()
    df.to_csv(output, index=include_index)
    blob_client = blob_service_client.get_blob_client(container=container, blob=blob_name)
    blob_client.upload_blob(output.getvalue().encode("utf-8"), overwrite=True)
    logging.info(f"Uploaded {blob_name} to container '{container}'.")


def transform_data(df: pd.DataFrame) -> pd.DataFrame:
    """Transform raw stock data into processed format."""
    df_transformed = df.copy()
    df_transformed["return_pct"] = df_transformed["Close"].pct_change()
    df_transformed.reset_index(inplace=True)
    return df_transformed


def main():
    """Main ETL pipeline logic."""
    logging.info("Starting ETL pipeline...")

    load_dotenv()  # only works locally, ignored in Azure
    raw_container = os.getenv("RAW_CONTAINER_NAME", "rawdata")
    processed_container = os.getenv("PROCESSED_CONTAINER_NAME", "processeddata")
    tickers_str = os.getenv("STOCK_TICKERS", "AAPL,MSFT,TSLA,GOOGL,AMZN")
    tickers = [t.strip() for t in tickers_str.split(",") if t.strip()]
    # API Key no longer needed for yfinance

    connection_string = os.getenv("AZURE_CONNECTION_STRING") or os.getenv("CONNECTION_STRING")
    if not connection_string:
        logging.error("AZURE_CONNECTION_STRING not found in environment variables.")
        raise ValueError("Azure connection string not found.")

    blob_service_client = BlobServiceClient.from_connection_string(connection_string)

    for ticker in tickers:
        try:
            df_raw = fetch_stock_data(ticker)
            if df_raw.empty:
                continue

            upload_to_azure(blob_service_client, raw_container, f"{ticker}_raw.csv", df_raw, include_index=True)

            df_processed = transform_data(df_raw)
            upload_to_azure(blob_service_client, processed_container, f"{ticker}_processed.csv", df_processed)

            # Avoid hitting rate limits
            time.sleep(15)
        except Exception as e:
            logging.error(f"Error processing {ticker}: {e}", exc_info=True)

    logging.info("ETL pipeline completed successfully.")
    
    # Run AI Enhancements
    logging.info("Starting AI Enhancements...")
    try:
        ai_insights.run_ai_pipeline(blob_service_client, processed_container)
    except Exception as e:
        logging.error(f"AI Insights failed: {e}")

    try:
        lstm_predictor.run_lstm_pipeline(blob_service_client, processed_container)
    except Exception as e:
        logging.error(f"LSTM Prediction failed: {e}")



if __name__ == "__main__":
    main()
