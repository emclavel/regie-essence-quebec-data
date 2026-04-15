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

response = requests.get(URL, headers=headers, timeout=30)
response.raise_for_status()

# requests gère la décompression automatiquement
data = response.json()

def get_price(fuels, fuel_code):
    """
    Extrait un prix numérique à partir de la structure fuel.
    Retourne None si absent ou non disponible.
    """
    for fuel in fuels:
        if fuel.get("code") == fuel_code:
            value = fuel.get("price")
            try:
                return float(value)
            except (TypeError, ValueError):
                return None
    return None

with open(OUTPUT_PATH, "w", newline="", encoding="utf-8") as csvfile:
    writer = csv.writer(csvfile)

    # ✅ EN-TÊTES IDENTIQUES À L’EXCEL (noms normalisés CSV)
    writer.writerow([
        "Nom",
        "Bannière",
        "Adresse",
        "Région",
        "Code_postal",
        "Latitude",
        "Longitude",
        "Prix_regulier",
        "Prix_super",
        "Prix_diesel"
    ])

    for feature in data.get("features", []):
        props = feature.get("properties", {})
        coords = feature["geometry"]["coordinates"]

        fuels = props.get("fuels", [])

        writer.writerow([
            props.get("name"),
            props.get("brand"),
            props.get("address"),
            props.get("region"),
            props.get("postalCode"),
            coords[1],  # latitude
            coords[0],  # longitude
            get_price(fuels, "REGULAR"),
            get_price(fuels, "SUPER"),
            get_price(fuels, "DIESEL"),
        ])
