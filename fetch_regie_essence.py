import os
import requests
import csv
from datetime import datetime

URL = "https://regieessencequebec.ca/stations.geojson.gz"
OUTPUT_PATH = "data/regie_essence_quebec.csv"

os.makedirs("data", exist_ok=True)

headers = {
    "User-Agent": "Mozilla/5.0 (compatible; data-ingestion/1.0)",
    "Accept": "application/json"
}

response = requests.get(URL, headers=headers, timeout=60)
response.raise_for_status()

data = response.json()

with open(OUTPUT_PATH, "w", newline="", encoding="utf-8") as csvfile:
    writer = csv.writer(csvfile)

    writer.writerow([
        "Nom",
        "Banniere",
        "Adresse",
        "Region",
        "Code_postal",
        "Latitude",
        "Longitude",
        "Prix_regulier",
        "Prix_super",
        "Prix_diesel",
        "date_import"
    ])

    for feature in data.get("features", []):
        props = feature.get("properties", {})
