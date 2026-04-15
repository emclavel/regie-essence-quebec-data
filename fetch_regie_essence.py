import os
import requests
import csv
import json
import gzip
from io import BytesIO
from datetime import datetime
from collections import defaultdict

URL = "https://regieessencequebec.ca/stations.geojson.gz"

OUTPUT_MAIN = "data/regie_essence_quebec.csv"
OUTPUT_GRAND_MONTREAL = "data/regie_essence_grand_montreal.csv"
OUTPUT_REGION_QUEBEC = "data/regie_essence_region_quebec.csv"

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

# ------------------------------------------------------------------
# Utilitaires
# ------------------------------------------------------------------

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


def write_csv(path, rows):
    with open(path, "w", newline="", encoding="utf-8") as csvfile:
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

        for r in rows:
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

# ------------------------------------------------------------------
# 1️⃣ Collecte par région
# ------------------------------------------------------------------

rows_by_region = defaultdict(list)

# ✅ date formatée SANS secondes
date_import = datetime.utcnow().strftime("%Y-%m-%d %H:%M")

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
        "rang_region": None,
        "highlight_carte": "",
        "date_import": date_import
    }

    rows_by_region[row["Region"]].append(row)

# ------------------------------------------------------------------
# 2️⃣ Calcul du rang régional + top 5 + égalités
# ------------------------------------------------------------------

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
        row["highlight_carte"] = "oui" if current_rank == 1 else ""

    if len(rows_sorted) <= 5:
        final_rows.extend(rows_sorted)
        continue

    cutoff_price = rows_sorted[4]["Prix_regulier"]

    final_rows.extend([
        r for r in rows_sorted
        if r["Prix_regulier"] <= cutoff_price
    ])

print(f"Lignes finales (QC) : {len(final_rows)}")

# ------------------------------------------------------------------
# 3️⃣ Écriture du CSV principal
# ------------------------------------------------------------------

write_csv(OUTPUT_MAIN, final_rows)

# ------------------------------------------------------------------
# 4️⃣ CSV supplémentaires par regroupement régional
# ------------------------------------------------------------------

REGIONS_GRAND_MONTREAL = [
    "Montréal",
    "Laval",
    "Montérégie",
    "Laurentides",
    "Lanaudière"
]

REGIONS_REGION_QUEBEC = [
    "Capitale-Nationale",
    "Chaudière-Appalaches"
]

rows_grand_montreal = [
    r for r in final_rows
    if r["Region"] in REGIONS_GRAND_MONTREAL
]

rows_region_quebec = [
    r for r in final_rows
    if r["Region"] in REGIONS_REGION_QUEBEC
]

write_csv(OUTPUT_GRAND_MONTREAL, rows_grand_montreal)
write_csv(OUTPUT_REGION_QUEBEC, rows_region_quebec)

print(f"CSV Grand Montréal : {len(rows_grand_montreal)} lignes")
print(f"CSV Région de Québec : {len(rows_region_quebec)} lignes")
