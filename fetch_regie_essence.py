import os
import requests
import csv
from datetime import datetime

URL = "https://regieessencequebec.ca/stations.geojson.gz"
CSV_PATH = "data/regie_essence_quebec.csv"

os.makedirs("data", exist_ok=True)

headers = {
    "User-Agent": "Mozilla/5.0 (compatible; data-ingestion/1.0)",
    "Accept": "application/json"
}

response = requests.get(URL, headers=headers, timeout=30)
response.raise_for_status()

# requests gère automatiquement la décompression gzip
data = response.json()

with open(CSV_PATH, "w", newline="", encoding="utf-8") as csvfile:
    writer = csv.writer(csvfile)

    # EN-TÊTES ALIGNÉES AVEC LE SCHÉMA RÉEL
    writer.writerow([
        "nom_station",
        "banniere",
        "adresse",
        "municipalite",
        "mrc",
        "code_postal",
        "prix_regulier",
        "prix_super",
        "prix_diesel",
        "longitude",
        "latitude",
        "date_mise_a_jour",
        "date_import"
    ])

    for feature in data["features"]:
        props = feature.get("properties", {})
        coords = feature["geometry"]["coordinates"]

        writer.writerow([
            props.get("name"),
            props.get("banner"),
            props.get("address"),
            props.get("municipality"),
            props.get("mrc"),
            props.get("postal_code"),
            props.get("price_regular"),
            props.get("price_super"),
            props.get("price_diesel"),
            coords[0],
            coords[1],
            props.get("updated_at"),
            datetime.utcnow().isoformat()
        ])
