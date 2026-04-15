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
    "User-Agent": "Mozilla/5.0",
    "Accept": "*/*"
}

response = requests.get(URL, headers=headers, timeout=60)
response.raise_for_status()
raw = response.content

# Gérer JSON gzip OU non gzip
if raw.lstrip().startswith(b"{"):
    data = json.loads(raw.decode("utf-8"))
else:
    with gzip.open(BytesIO(raw), "rt", encoding="utf-8") as f:
        data = json.load(f)

features = data.get("features", [])

print(f"Nombre de stations détectées : {len(features)}")

def extract_prices(prices_list):
    prix_regulier = None
    prix_super = None
    prix_diesel = None

    for item in prices_list:
        gas_type = item.get("GasType")
        price = item.get("Price")
        available = item.get("IsAvailable", False)

        if not available or not price:
            continue

        try:
            numeric_price = float(price.replace("¢", "").strip())
        except ValueError:
            continue

        if gas_type == "Régulier":
            prix_regulier = numeric_price
        elif gas_type == "Super":
            prix_super = numeric_price
        elif gas_type == "Diesel":
            prix_diesel = numeric_price

    return prix_regulier, prix_super, prix_diesel

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
        prices_list = props.get("Prices", [])

        prix_regulier, prix_super, prix_diesel = extract_prices(prices_list)

        writer.writerow([
            props.get("Name"),
            props.get("brand"),
            props.get("Address"),
            props.get("Region"),
            props.get("PostalCode"),
            coords[1],  # latitude
            coords[0],  # longitude
            prix_regulier,
            prix_super,
            prix_diesel,
            datetime.utcnow().isoformat()
        ])
