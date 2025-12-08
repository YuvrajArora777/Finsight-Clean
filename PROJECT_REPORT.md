# FinSight: Technical Implementation Report 🚀

## 1. Executive Summary
**FinSight** is an end-to-end financial intelligence platform designed to democratize stock analysis. It combines **Real-Time Data Engineering** with **Agentic AI** to provide actionable insights. The system moves beyond simple charting by integrating **LSTM Predictive Models** and a **Context-Aware Chatbot (FinBot)**.

---

## 2. System Architecture: The "Hybrid" Approach 🏗️
We evolved the architecture from a simple cloud script to a robust hybrid system to optimize for both **Speed** and **Compute Power**.

### A. Data Layer (Sources)
*   **Primary Source**: **Yahoo Finance (`yfinance`)**.
    *   *Decision*: We migrated from Alpha Vantage to `yfinance` to overcome the critical "25 requests/day" rate limit. This ensures our dashboard always has access to unlimited, split-adjusted historical data.
*   **Storage**: **Azure Blob Storage**.
    *   Acts as our "Data Lake". Stores Raw Data, Processed Datasets, and Pre-computed AI outputs (`ai_insights.csv`, `lstm_predictions.csv`).

### B. The Backend (The "Brain") 🧠
*   **Host**: **Azure Functions** (Serverless).
*   **Schedule**: Runs automatically every **6 hours**.
*   **Workflow**:
    1.  **Extract**: Fetches latest history for Apple, Tesla, Amazon, etc.
    2.  **Transform**: Cleans data and calculates technical indicators (RSI, MA).
    3.  **Predict**: Runs the LSTM Model to forecast next-day closing prices.
    4.  **Analyze**: Uses OpenAI (GPT-4o) to generate textual summaries of market trends.

### C. The Frontend (The "Face") 💻
*   **Host**: **Streamlit Community Cloud**.
*   **Technology**: Python (Streamlit) + Plotly.
*   **Why Streamlit Cloud?**:
    *   We initially attempted Azure App Service deployment but encountered strict **Regional Policy Restrictions** on the Azure Student subscription.
    *   **Pivot**: Migrated frontend hosting to Streamlit Cloud for zero-cost, high-availability hosting that connects securely to the Azure backend.

---

## 3. Key Challenges & Solutions 🛠️

| Challenge | Impact | Technical Solution |
| :--- | :--- | :--- |
| **API Rate Limits** | Alpha Vantage blocked updates after 5 calls, leaving data stale (Dec 4th). | **Refactored ETL Pipeline** to use `yfinance` library, enabling unlimited data fetching without API keys. |
| **Deployment Blockers** | Azure Policy blocked resource creation in `Central India`, `East US`, etc. | **Strategic Pivot**: Decoupled the frontend. Deployed Dashboard to Streamlit Cloud while keeping the Backend on Azure. |
| **Git & Secrets** | Active secret file (`local.settings.json`) prevented GitHub Push. | **Git History Rewrite**: Used `git reset` to unstage the file, added it to `.gitignore`, and force-pushed a clean history. |
| **Latency** | Reading live prices from Azure Blob was too slow (minutes old). | **Real-Time Fetching**: Updated `app.py` to fetch *Price* data directly from Yahoo on page load (ms latency) while loading *AI* data from Azure. |

---

## 4. Final Deliverables ✅
1.  **Codebase**: A clean, modular Python project structure (`etl_pipeline`, `dashboard`, `lstm`).
2.  **Security**: All secrets (Azure Keys, OpenAI Keys) are abstracted into Environment Variables and Streamlit Secrets.
3.  **Documentation**:
    *   `README.md`: Setup and Installation guide.
    *   `walkthrough.md`: User manual for the dashboard.
    *   `deployment.md`: Guide for reproducing the deployment.

---
*Generated for Major Project Submission*
