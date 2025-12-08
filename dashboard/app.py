import streamlit as st
import pandas as pd
import plotly.graph_objects as go
from azure.storage.blob import BlobServiceClient
import os
from dotenv import load_dotenv
from io import StringIO
import chat_logic
import yfinance as yf

# Page Config
st.set_page_config(page_title="FinSight Analyst Portal", layout="wide", page_icon="📈")
load_dotenv()

# --- HELPER FUNCTIONS ---
@st.cache_resource
def get_blob_service_client():
    connection_string = os.getenv("AZURE_CONNECTION_STRING") or os.getenv("CONNECTION_STRING")
    if not connection_string:
        st.error("Missing Azure Connection String in .env")
        return None
    return BlobServiceClient.from_connection_string(connection_string)

@st.cache_data(ttl=60) # Cache for 1 min (near real-time)
def load_data(ticker):
    """Fetch data directly from Yahoo Finance for real-time updates."""
    try:
        # Download last 2 years of data
        df = yf.download(ticker, period="2y", interval="1d", auto_adjust=True, progress=False)
        
        if df.empty:
            return pd.DataFrame()

        # Handle MultiIndex columns if present
        if isinstance(df.columns, pd.MultiIndex):
            df.columns = df.columns.droplevel(1)
            
        # Ensure standard columns
        required_cols = ["Open", "High", "Low", "Close", "Volume"]
        available_cols = [c for c in required_cols if c in df.columns]
        df = df[available_cols]
        
        # Ensure DateTime Index
        df.index = pd.to_datetime(df.index)
        return df
    except Exception as e:
        st.error(f"Error loading {ticker} from Yahoo: {e}")
        return pd.DataFrame()

@st.cache_data(ttl=600)
def load_insights():
    client = get_blob_service_client()
    if not client: return pd.DataFrame()
    
    try:
        container = os.getenv("PROCESSED_CONTAINER_NAME", "processeddata")
        blob_client = client.get_blob_client(container=container, blob="ai_insights.csv")
        if not blob_client.exists(): return pd.DataFrame()
        
        download_stream = blob_client.download_blob()
        return pd.read_csv(StringIO(download_stream.content_as_text()))
    except:
        return pd.DataFrame()

@st.cache_data(ttl=600)
def load_predictions():
    client = get_blob_service_client()
    if not client: return pd.DataFrame()
    
    try:
        container = os.getenv("PROCESSED_CONTAINER_NAME", "processeddata")
        blob_client = client.get_blob_client(container=container, blob="lstm_predictions.csv")
        if not blob_client.exists(): return pd.DataFrame()
        
        download_stream = blob_client.download_blob()
        return pd.read_csv(StringIO(download_stream.content_as_text()))
    except:
        return pd.DataFrame()

# --- MAIN UI ---
st.title("📈 FinSight Analyst Portal")
st.markdown("Real-time Financial Intelligence Dashboard")

# Sidebar
st.sidebar.header("Configuration")
view_mode = st.sidebar.radio("View Mode", ["Deep Dive", "Comparison View"])
tickers_str = os.getenv("STOCK_TICKERS", "AAPL,MSFT,TSLA,GOOGL,AMZN")
tickers = [t.strip() for t in tickers_str.split(",") if t.strip()]

if view_mode == "Deep Dive":
    selected_ticker = st.sidebar.selectbox("Select Ticker", tickers)
else:
    selected_tickers = st.sidebar.multiselect("Select Tickers", tickers, default=tickers[:3])


if view_mode == "Deep Dive":
    # Load Data
    df = load_data(selected_ticker)
    all_insights = load_insights()
    all_predictions = load_predictions()

    if df.empty:
        st.warning(f"No data found for {selected_ticker}. Please ensure the ETL pipeline has run.")
    else:
        # 0. Health Indicator
        last_update = df.index[-1].strftime('%Y-%m-%d')
        st.caption(f"🟢 System Status: Online | Latest Data: {last_update}")

        # 1. KPI Metrics
        latest = df.iloc[-1]
        prev = df.iloc[-2]
        change_val = latest["Close"] - prev["Close"]
        change_pct = (change_val / prev["Close"]) * 100
        
        col1, col2, col3, col4 = st.columns(4)
        col1.metric("Current Price", f"${latest['Close']:.2f}", f"{change_val:.2f} ({change_pct:.2f}%)")
        col2.metric("Volume", f"{int(latest['Volume']):,}")
        
        # Prediction KPI
        if not all_predictions.empty:
            pred_row = all_predictions[all_predictions["Ticker"] == selected_ticker]
            if not pred_row.empty:
                p_price = float(pred_row.iloc[0]["Predicted 1D Price"])
                p_dir = pred_row.iloc[0]["Direction"]
                col3.metric("AI Prediction (Next Day)", f"${p_price:.2f}", p_dir, delta_color="normal")

        # Insight KPI
        if not all_insights.empty:
            insight_row = all_insights[all_insights["Ticker"] == selected_ticker]
            if not insight_row.empty:
                st.info(f"**AI Insight**: {insight_row.iloc[0]['Insight']}")

        # 2. Charts
        tab1, tab2 = st.tabs(["Price Action", "Volume Analysis"])
        
        with tab1:
            fig = go.Figure(data=[go.Candlestick(x=df.index,
                            open=df['Open'],
                            high=df['High'],
                            low=df['Low'],
                            close=df['Close'])])
            fig.update_layout(title=f"{selected_ticker} Price Chart", height=500)
            st.plotly_chart(fig, use_container_width=True)

        with tab2:
            fig_vol = go.Figure(data=[go.Bar(x=df.index, y=df['Volume'], marker_color='teal')])
            fig_vol.update_layout(title=f"{selected_ticker} Trading Volume", height=500)
            st.plotly_chart(fig_vol, use_container_width=True)

    # --- CHATBOT SECTION (Only in Deep Dive) ---
    st.divider()
    st.subheader(f"💬 Chat with FinBot ({selected_ticker})")

    if "messages" not in st.session_state:
        st.session_state.messages = []

    # Display chat history
    for message in st.session_state.messages:
        with st.chat_message(message["role"]):
            st.markdown(message["content"])

    # User Input
    if prompt := st.chat_input(f"Ask about {selected_ticker}..."):
        st.session_state.messages.append({"role": "user", "content": prompt})
        with st.chat_message("user"):
            st.markdown(prompt)

        # Prepare prediction context
        pred_context = None
        if not all_predictions.empty:
            p_row = all_predictions[all_predictions["Ticker"] == selected_ticker]
            if not p_row.empty:
                pred_context = {
                    "price": float(p_row.iloc[0]["Predicted 1D Price"]),
                    "direction": p_row.iloc[0]["Direction"]
                }
        
        # Prepare Market Context for Comparison
        # "AAPL: $150 (+1.2%), TSLA: $200 (-0.5%)"
        market_context_str = ""
        for t in tickers:
            if t == selected_ticker: continue # skip current
            d_t = load_data(t)
            if not d_t.empty:
                l_t = d_t.iloc[-1]['Close']
                p_t = d_t.iloc[-2]['Close']
                c_pct = ((l_t - p_t) / p_t) * 100
                market_context_str += f"{t}: ${l_t:.2f} ({c_pct:+.2f}%), "
        
        # Generate Response
        with st.chat_message("assistant"):
            response = chat_logic.generate_chat_response(
                st.session_state.messages, 
                selected_ticker, 
                df.tail(60) if not df.empty else pd.DataFrame(),
                prediction=pred_context,
                market_context=market_context_str
            )
            st.markdown(response)
        
        st.session_state.messages.append({"role": "assistant", "content": response})

else: 
    # --- COMPARISON VIEW ---
    st.subheader("📊 Market Comparison")
    
    if not selected_tickers:
        st.warning("Please select at least one ticker.")
    else:
        # Load all data
        comp_data = {}
        for t in selected_tickers:
            df_t = load_data(t)
            if not df_t.empty:
                comp_data[t] = df_t
        
        if not comp_data:
            st.error("No data available for selected tickers.")
        else:
            # 1. Normalized Price Chart (Rebased to 0%)
            st.caption("Normalized Return % (Last 60 Days)")
            fig_comp = go.Figure()
            
            for t, df_t in comp_data.items():
                if len(df_t) > 0:
                    # Normalize to first day = 0%
                    start_price = df_t['Close'].iloc[0]
                    norm_series = ((df_t['Close'] - start_price) / start_price) * 100
                    fig_comp.add_trace(go.Scatter(x=df_t.index, y=norm_series, mode='lines', name=t))

            fig_comp.update_layout(
                title="Relative Performance Comparison (%)",
                xaxis_title="Date",
                yaxis_title="Return %",
                hovermode="x unified",
                height=600
            )
            st.plotly_chart(fig_comp, use_container_width=True)
            
            # 2. Volume Comparison
            st.caption("Trading Volume Comparison")
            fig_vol_comp = go.Figure()
            for t, df_t in comp_data.items():
                fig_vol_comp.add_trace(go.Bar(x=df_t.index, y=df_t['Volume'], name=t))
            
            fig_vol_comp.update_layout(title="Volume Comparison", barmode='group', height=400)
            st.plotly_chart(fig_vol_comp, use_container_width=True)
