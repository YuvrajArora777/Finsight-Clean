import os
from azure.storage.blob import BlobServiceClient
from dotenv import load_dotenv
import pandas as pd
from io import StringIO

load_dotenv()
conn_str = os.getenv("AZURE_CONNECTION_STRING") or os.getenv("CONNECTION_STRING")
container = os.getenv("PROCESSED_CONTAINER_NAME", "processeddata")
client = BlobServiceClient.from_connection_string(conn_str)
blob_client = client.get_blob_client(container=container, blob="AAPL_processed.csv")

if blob_client.exists():
    data = blob_client.download_blob().content_as_text()
    df = pd.read_csv(StringIO(data), index_col=0)
    print(f"LATEST DATE IN CLOUD (AAPL): {df.index[-1]}")
else:
    print("BLOB NOT FOUND")
