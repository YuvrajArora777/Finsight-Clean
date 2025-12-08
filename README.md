# FinSight 📈
**Automated Financial Intelligence Pipeline & Analyst Portal**

FinSight is an end-to-end financial data engineering project that automates the extraction, processing, and analysis of stock market data. It combines robust cloud infrastructure (Azure) with modern "Agentic AI" (OpenAI + LSTM) to deliver real-time insights and predictions.

## 🚀 Features

### 1. Cloud ETL Pipeline (Azure)
*   **Source**: Alpha Vantage API (Daily Stock Data).
*   **Orchestration**: Azure Functions (Timer Trigger runs every 6 hours).
*   **Storage**: Azure Blob Storage (Raw & Processed Data Layers).
*   **Transformation**: Pandas-based cleaning and feature engineering (Return %, Volatility).

### 2. AI & Machine Learning
*   **Smart Insights (RAG)**: Uses **OpenAI GPT-4o-mini** to read processed data and generate professional financial commentary (e.g., "TSLA showing high volatility...").
*   **Predictive Modeling (LSTM)**: A TensorFlow/Keras LSTM model trains on-the-fly to predict the **next day's closing price** and trend direction.

### 3. Analyst Portal (Dashboard)
A modern, interactive frontend built with **Streamlit** and **Plotly**.
*   **Deep Dive Mode**: detailed charts, AI predictions, and a **"Chat with Data"** bot.
*   **Comparison Mode**: Compare normalized returns of multiple stocks side-by-side.
*   **FinBot**: Context-aware chatbot that answers questions about specific stocks using the live data.

---

## 🏗️ Architecture

```mermaid
graph TD
    API[Alpha Vantage API] -->|Fetch| Function[Azure Function (Python)]
    Function -->|Raw CSV| Blob[Azure Blob Storage]
    
    subgraph "ETL & AI Layer"
    Function -->|Transform| Processed[Processed Data]
    Processed -->|Context| OpenAI[OpenAI GPT-4o]
    Processed -->|Train| LSTM[LSTM Model]
    OpenAI -->|Insights| Blob
    LSTM -->|Predictions| Blob
    end

    subgraph "Frontend"
    Blob -->|Read| Dashboard[Streamlit Analyst Portal]
    Dashboard -->|Interact| User[User]
    end
```

---

## 🛠️ Installation & Setup

### Prerequisites
*   Python 3.10+
*   Azure Storage Account (Connection String)
*   Alpha Vantage API Key
*   OpenAI API Key

### 1. Clone & Install
```bash
git clone https://github.com/yourusername/finsight.git
cd finsight
pip install -r requirements.txt
```

### 2. Configure Environment
Create a `.env` file in the root directory:
```ini
AZURE_CONNECTION_STRING="your_azure_connection_string"
ALPHAVANTAGE_API_KEY="your_alpha_vantage_key"
OPENAI_API_KEY="your_openai_key"
STOCK_TICKERS="AAPL,MSFT,TSLA,GOOGL,AMZN"
```

### 3. Run the Dashboard
```bash
python -m streamlit run dashboard/app.py
```
Visit `http://localhost:8501` in your browser.

---

## 📂 Project Structure
*   `etl_pipeline/`: Core ETL logic, AI generators, and LSTM predictors.
*   `function_app.py`: Azure Function trigger configuration.
*   `dashboard/`: Streamlit frontend code (`app.py`) and Chatbot logic (`chat_logic.py`).

---

## 🔮 Future Roadmap
*   Deploy Dashboard to Azure App Service / Streamlit Cloud.
*   Add Sentiment Analysis on News Headlines.
*   Expand to Crypto & Forex markets.
