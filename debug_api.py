import requests
import os
from dotenv import load_dotenv
import json

load_dotenv()
api_key = os.getenv("ALPHAVANTAGE_API_KEY")
ticker = "AAPL"
url = f"https://www.alphavantage.co/query?function=TIME_SERIES_DAILY_ADJUSTED&symbol={ticker}&outputsize=compact&apikey={api_key}"

print(f"Querying {url}...")
r = requests.get(url)
data = r.json()

if "Time Series (Daily)" in data:
    dates = list(data["Time Series (Daily)"].keys())
    print(f"Latest 5 dates from API: {dates[:5]}")
else:
    print("Error / No Data:", data)
