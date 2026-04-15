import os
import requests
import pandas as pd
from io import BytesIO

URL = "https://regieessencequebec.ca/data/stations.xlsx"
OUTPUT_PATH = "data/regie_essence_quebec.csv"

os.makedirs("data", exist_ok=True)

response = requests.get(URL, timeout=60)
response.raise_for_status()

df = pd.read_excel(BytesIO(response.content))

df = df.rename(columns={
    "Nom": "Nom",
    "Bannière": "Bannière",
    "Adresse": "Adresse",
    "Région": "Région",
    "Code Postal": "Code_postal",
    "Latitude": "Latitude",
    "Longitude": "Longitude",
    "Prix Régulier": "Prix_regulier",
    "Prix Super": "Prix_super",
    "Prix Diesel": "Prix_diesel"
})

def clean_price(value):
    if isinstance(value, str):
        value = value.replace("¢", "").strip()
        if value.upper() == "N/D":
            return None
    try:
        return float(value)
    except Exception:
        return None

for col in ["Prix_regulier", "Prix_super", "Prix_diesel"]:
    df[col] = df[col].apply(clean_price)

df.to_csv(OUTPUT_PATH, index=False, encoding="utf-8")
