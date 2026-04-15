import os
import requests
import csv
import gzip
import json
from io import BytesIO
from datetime import datetime

URL = "https://regieessencequebec.ca/stations.geojson.gz"
OUTPUT_PATH = "data/regie_essence_quebec.csv"

os.makedirs("data", exist_ok=True)

headers = {
    "User-Agent": "Mozilla/5.0 (compatible; data-ingestion/1.0)",
    "Accept": "application/gzip"
}

response = requests.get(URL, headers=headers, timeout=60)
response.raise_for_status()

# ✅ Décompression explicite du GZIP
with gzip.open(BytesIO(response.content), "rt", encoding="utf-8") as f:
    data = json.load(f)

features = data.get("features", [])

print(f"Nombre de stations détectées : {len(features)}")

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

    for feature in features:
        props = feature.get("properties", {})
        coords = feature.get("geometry", {}).get("coordinates", [None, None])
        prices = props.get("prices", {})

        writer.writerow([
            props.get("name"),
            props.get("brand"),
            props.get("address"),
            props.get("region"),
            props.get("postal_code"),
            coords[1],  # latitude
            coords[0],  # longitude
            prices.get("regular"),
            prices.get("super"),
            prices.get("diesel"),
            datetime.utcnow().isoformat()
        ])
