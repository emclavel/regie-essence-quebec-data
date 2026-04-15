import os
import requests
import csv
import json
import gzip
from io import BytesIO
from datetime import datetime

URL = "https://regieessencequebec.ca/stations.geojson.gz"
OUTPUT_PATH = "data/regie_essence_quebec.csv"

os.makedirs("data", exist_ok=True)

headers = {
    "User-Agent": "Mozilla/5.0 (compatible; data-ingestion/1.0)",
    "Accept": "*/*"
}

response = requests.get(URL, headers=headers, timeout=60)
response.raise_for_status()

raw = response.content

# ✅ Détection automatique du format
try:
    if raw.lstrip().startswith(b"{"):
        # JSON non compressé
        data = json.loads(raw.decode("utf-8"))
    else:
        # JSON compressé gzip
        with gzip.open(BytesIO(raw), "rt", encoding="utf-8") as f:
            data = json.load(f)
except Exception as e:
    raise RuntimeError(f"Impossible de parser le GeoJSON: {e}")

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
            coords[1] if len(coords) > 1 else None,
            coords[0] if len(coords) > 0 else None,
            prices.get("regular"),
            prices.get("super"),
            prices.get("diesel"),
            datetime.utcnow().isoformat()
        ])
