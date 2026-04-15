import os
import requests
import csv
import json
import gzip
from io import BytesIO
from datetime import datetime
from collections import defaultdict

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

# Détection gzip / non gzip
if raw.lstrip().startswith(b"{"):
    data = json.loads(raw.decode("utf-8"))
else:
    with gzip.open(BytesIO(raw), "rt", encoding="utf-8") as f:
        data = json.load(f)

features = data.get("features", [])
print(f"Stations totales détectées : {len(features)}")

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

# 1️⃣ Collecte par région
rows_by_region = defaultdict(list)

for feature in features:
    props = feature.get("properties", {})
    coords = feature.get("geometry", {}).get("coordinates", [None, None])
    prices_list = props.get("Prices", [])

    prix_regulier, prix_super, prix_diesel = extract_prices(prices_list)

    if prix_regulier is None:
        continue

    row = {
        "Nom": props.get("Name"),
        "Banniere": props.get("brand"),
        "Adresse": props.get("Address"),
        "Region": props.get("Region"),
        "Code_postal": props.get("PostalCode"),
        "Latitude": coords[1],
        "Longitude": coords[0],
        "Prix_regulier": prix_regulier,
        "Prix_super": prix_super,
        "Prix_diesel": prix_diesel,
        "rang_region": None,   # calculé plus loin
        "highlight_carte": None,  # ✅ NOUVELLE COLONNE
        "date_import": datetime.utcnow().isoformat()
    }

    rows_by_region[row["Region"]].append(row)

# 2️⃣ Calcul du rang régional + sélection top 5 + égalités
final_rows = []

for region, rows in rows_by_region.items():
    rows_sorted = sorted(rows, key=lambda r: r["Prix_regulier"])

    current_rank = 0
    last_price = None

    for idx, row in enumerate(rows_sorted):
        if row["Prix_regulier"] != last_price:
            current_rank = idx + 1
            last_price = row["Prix_regulier"]

        row["rang_region"] = current_rank

        # ✅ LOGIQUE IF demandée
        row["highlight_carte"] = "oui" if current_rank == 1 else ""

    # Sélection top 5 + égalités
    if len(rows_sorted) <= 5:
        final_rows.extend(rows_sorted)
        continue

    cutoff_price = rows_sorted[4]["Prix_regulier"]

    top_with_equals = [
        r for r in rows_sorted if r["Prix_regulier"] <= cutoff_price
    ]

    final_rows.extend(top_with_equals)

print(f"Lignes finales retenues : {len(final_rows)}")

# 3️⃣ Écriture du CSV
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
        "rang_region",
        "highlight_carte",
        "date_import"
    ])

    for r in final_rows:
        writer.writerow([
            r["Nom"],
            r["Banniere"],
            r["Adresse"],
            r["Region"],
            r["Code_postal"],
            r["Latitude"],
            r["Longitude"],
            r["Prix_regulier"],
            r["Prix_super"],
            r["Prix_diesel"],
            r["rang_region"],
            r["highlight_carte"],
            r["date_import"]
        ])
