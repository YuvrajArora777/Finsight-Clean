# FinSight 📈
**Automated Financial Intelligence Pipeline & Analyst Portal**

FinSight is an end-to-end financial data engineering project that automates the extraction, processing, and analysis of stock market data. It combines robust cloud infrastructure (Azure) with modern "Agentic AI" (OpenAI + LSTM) to deliver real-time insights and predictions.

## 🚀 Features

### 1. Cloud ETL Pipeline (Azure)
*   **Source**: **Yahoo Finance API** (Unlimited Daily Stock Data).
*   **Orchestration**: Azure Functions (Timer Trigger runs every 6 hours).
*   **Storage**: Azure Blob Storage (Raw & Processed Data Layers).
*   **Tech Stack**: Python V2 Model, `tensorflow-cpu` (Optimized for Serverless).

### 2. AI & Machine Learning
*   **Smart Insights (RAG)**: Uses **OpenAI GPT-4o-mini** to read processed data and generate professional financial commentary (e.g., "TSLA showing high volatility...").
*   **Predictive Modeling (LSTM)**: A TensorFlow/Keras LSTM model trains on-the-fly to predict the **next day's closing price** and trend direction.

### 3. Analyst Portal (Dashboard)
A modern, interactive frontend built with **Streamlit** and **Plotly**.
*   **Hybrid Data Architecture**: Fetches **Real-Time Prices** directly from Yahoo Finance while pulling **AI Insights** from Azure Blob Storage.
*   **FinBot**: Context-aware chatbot that answers questions about specific stocks using the live data.

---

## 🏗️ Architecture

```mermaid
graph TD
    subgraph "Frontend - Streamlit Cloud"
    User[User] -->|Interact| Dashboard[Analyst Portal]
    Dashboard -->|Fetch Live Prices| Yahoo[Yahoo Finance API]
    end

    subgraph "Backend - Azure Functions"
    Timer[Timer Trigger (6-hr)] -->|Start| ETL[ETL Pipeline]
    ETL -->|Fetch History| Yahoo
    ETL -->|Raw CSV| Blob[Azure Blob Storage]
    ETL -->|Transform| Processed[Processed Data]
    Processed -->|Context| OpenAI[OpenAI GPT-4o]
    Processed -->|Train| LSTM[LSTM Model]
    OpenAI -->|Insights| Blob
    LSTM -->|Predictions| Blob
    end

    Blob -->|Read AI Data| Dashboard
```

---

## 🛠️ Installation & Setup

### Prerequisites
*   Python 3.10+
*   Azure Storage Account (Connection String)
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

## 🔮 Roadmap
*   Deploy Dashboard to Streamlit Cloud.
*   Add Sentiment Analysis on News Headlines.
*   Expand to Crypto & Forex markets.
