import logging
import os
import pandas as pd
import numpy as np
from io import StringIO
from azure.storage.blob import BlobServiceClient
from sklearn.preprocessing import MinMaxScaler

# NOTICE: TensorFlow imports removed from top-level to prevent Serverless Cold-Start timeouts.
# They are now lazy-loaded inside the functions that need them.

def create_dataset(dataset, look_back=60):
    """Convert an array of values into a dataset matrix."""
    X, Y = [], []
    for i in range(len(dataset) - look_back - 1):
        a = dataset[i:(i + look_back), 0]
        X.append(a)
        Y.append(dataset[i + look_back, 0])
    return np.array(X), np.array(Y)

def train_and_predict(df: pd.DataFrame, ticker: str):
    """Train a simple LSTM and predict the next day's price."""
    # Lazy Import TensorFlow here
    import tensorflow as tf
    from tensorflow.keras.models import Sequential
    from tensorflow.keras.layers import LSTM, Dense
    from tensorflow.keras.callbacks import EarlyStopping
    import numpy as np
    
    # Ensure we have enough data
    if len(df) < 100:
        logging.warning(f"Not enough data to train LSTM for {ticker}. Need > 100 rows.")
        return None

    data = df["Close"].values.reshape(-1, 1)
    scaler = MinMaxScaler(feature_range=(0, 1))
    scaled_data = scaler.fit_transform(data)

    # Train/Test Split logic (simplified for retraining on full data for next-day prediction)
    look_back = 60
    X_train, y_train = create_dataset(scaled_data, look_back)
    
    if len(X_train) == 0:
        return None

    # Reshape input to be [samples, time steps, features]
    X_train = np.reshape(X_train, (X_train.shape[0], X_train.shape[1], 1))

    # Build Model
    model = Sequential()
    model.add(LSTM(50, return_sequences=False, input_shape=(look_back, 1)))
    model.add(Dense(25))
    model.add(Dense(1))
    
    # Compile & Train (Fast training for demo)
    model.compile(optimizer='adam', loss='mean_squared_error')
    model.fit(X_train, y_train, batch_size=32, epochs=3, verbose=0) 

    # Predict Next Day
    last_60_days = scaled_data[-look_back:]
    X_test = np.reshape(last_60_days, (1, look_back, 1))
    predicted_scaled = model.predict(X_test, verbose=0)
    prediction = scaler.inverse_transform(predicted_scaled)
    
    return float(prediction[0][0])

def run_lstm_pipeline(blob_service_client: BlobServiceClient, processed_container: str):
    """Run LSTM predictions for all tickers."""
    logging.info("Starting LSTM Prediction Pipeline...")
    
    tickers_str = os.getenv("STOCK_TICKERS", "AAPL,MSFT,TSLA,GOOGL,AMZN")
    tickers = [t.strip() for t in tickers_str.split(",") if t.strip()]
    
    predictions = []

    for ticker in tickers:
        try:
            # Download processed data
            blob_name = f"{ticker}_processed.csv"
            blob_client = blob_service_client.get_blob_client(container=processed_container, blob=blob_name)
            
            if not blob_client.exists():
                continue

            download_stream = blob_client.download_blob()
            df = pd.read_csv(StringIO(download_stream.content_as_text()), index_col=0)
            
            pred_price = train_and_predict(df, ticker)
            
            if pred_price:
                current_price = df["Close"].iloc[-1]
                direction = "UP" if pred_price > current_price else "DOWN"
                pct_change = ((pred_price - current_price) / current_price) * 100
                
                predictions.append({
                    "Ticker": ticker, 
                    "Current Price": current_price,
                    "Predicted 1D Price": pred_price,
                    "Direction": direction,
                    "Predicted % Change": pct_change,
                    "Date": pd.Timestamp.now().strftime("%Y-%m-%d")
                })
                logging.info(f"LSTM Prediction for {ticker}: {pred_price:.2f} ({direction})")
            
        except Exception as e:
            logging.error(f"LSTM error for {ticker}: {e}")

    # Save predictions
    if predictions:
        pred_df = pd.DataFrame(predictions)
        output = StringIO()
        pred_df.to_csv(output, index=False)
        
        target_blob_client = blob_service_client.get_blob_client(container=processed_container, blob="lstm_predictions.csv")
        target_blob_client.upload_blob(output.getvalue().encode("utf-8"), overwrite=True)
        logging.info("Successfully uploaded lstm_predictions.csv to Azure.")
