import os
import requests
import csv
import gzip
import json
from io import BytesIO
from datetime import datetime

URL = "https://regieessencequebec.ca/stations.geojson.gz"
CSV_PATH = "data/regie_essence_quebec.csv"

os.makedirs("data", exist_ok=True)

headers = {
    "User-Agent": "Mozilla/5.0 (compatible; DatawrapperBot/1.0; +https://datawrapper.de)",
    "Accept": "application/gzip"
}

response = requests.get(URL, headers=headers, timeout=30)
response.raise_for_status()

with gzip.open(BytesIO(response.content), "rt", encoding="utf-8") as f:
    data = json.load(f)

with open(CSV_PATH, "w", newline="", encoding="utf-8") as csvfile:
    writer = csv.writer(csvfile)

    writer.writerow([
        "nom_station",
        "banniere",
        "adresse",
        "ville",
        "region",
        "prix_regulier",
        "prix_super",
        "prix_diesel",
        "longitude",
        "latitude",
        "updated_at",
        "date_import"
    ])

    for feature in data["features"]:
        props = feature.get("properties", {})
        coords = feature["geometry"]["coordinates"]
        prices = props.get("prices", {})

        writer.writerow([
            props.get("name"),
            props.get("brand"),
            props.get("address"),
            props.get("city"),
            props.get("region"),
            prices.get("regular"),
            prices.get("super"),
            prices.get("diesel"),
            coords[0],
            coords[1],
            props.get("updated_at"),
            datetime.utcnow().isoformat()
        ])
