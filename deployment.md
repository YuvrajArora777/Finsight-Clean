# Deployment Guide: Streamlit Cloud (Standard) 🎈

Since you have **Git installed**, we will use the standard, professional workflow.

---

## Phase 1: Push to GitHub
1.  **Open Source Control**: Click the "Source Control" icon in VS Code sidebar (looks like a graph node).
2.  **Initialize**: Click "Initialize Repository" (or `git init` in terminal).
3.  **Commit**:
    *   Type a message (e.g., "Initial commit").
    *   Click **Commit** (Checkmark icon).
    *   (If asked to stage changes, say "Yes" or "Always").
4.  **Publish to GitHub**:
    *   Click the "Publish Branch" button (cloud icon).
    *   Select **"Publish to public repository"** (simplest).
    *   Vs Code will handle the authentication and creation of the repo `finsight-clean` (or similar) for you.

---

## Phase 2: Deploy on Streamlit Cloud
1.  Go to [share.streamlit.io](https://share.streamlit.io/).
2.  Log in with GitHub.
3.  Click **"New app"**.
4.  **Repository**: Select the repo you just created (e.g., `finsight-clean`).
5.  **Branch**: `main` (or `master`).
6.  **Main file path**: `dashboard/app.py`.
7.  Click **Deploy!** 🚀

---

## Phase 3: Add Secrets (Critical)
Your app will fail initially because it doesn't have your keys.
1.  On your new app dashboard, click **"Manage app"** (bottom right) -> three dots `...` -> **Settings**.
2.  Go to **Secrets**.
3.  Paste the content below (Copy exact lines from your local `.env` file):

```toml
AZURE_CONNECTION_STRING = "..."
OPENAI_API_KEY = "..."
PROCESSED_CONTAINER_NAME = "processeddata"
STOCK_TICKERS = "AAPL,MSFT,TSLA,GOOGL,AMZN"
```

4.  Click **Save**.
5.  **Reboot**: Click the "Reboot app" button.

**Done!** You now have a public link to share.
