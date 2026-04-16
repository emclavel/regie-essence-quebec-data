import os
import requests
import csv
import json
import gzip
from io import BytesIO
from datetime import datetime
from zoneinfo import ZoneInfo
from collections import defaultdict

URL = "https://regieessencequebec.ca/stations.geojson.gz"

OUTPUT_MAIN = "data/regie_essence_quebec.csv"
OUTPUT_GRAND_MONTREAL = "data/regie_essence_grand_montreal.csv"
OUTPUT_REGION_QUEBEC = "data/regie_essence_region_quebec.csv"

# ➕ NOUVEAUX CSV
OUTPUT_MAURICIE = "data/regie_essence_mauricie.csv"
OUTPUT_ESTRIE = "data/regie_essence_estrie.csv"
OUTPUT_SAG_LSJ = "data/regie_essence_saguenay_lac_st_jean.csv"

os.makedirs("data", exist_ok=True)

headers = {
    "User-Agent": "Mozilla/5.0",
    "Accept": "*/*"
}

response = requests.get(URL, headers=headers, timeout=60)
response.raise_for_status()
raw = response.content

# ------------------------------------------------------------------
# Détection gzip / non gzip
# ------------------------------------------------------------------

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
            "is_ghost",
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
                r["is_ghost"],
                r["date_import"]
            ])


def add_ghost_points(rows, region_name, bbox):
    north, south, west, east = bbox

    ghosts = [
        ("ghost_north", north, (west + east) / 2),
        ("ghost_south", south, (west + east) / 2),
        ("ghost_west",  (north + south) / 2, west),
        ("ghost_east",  (north + south) / 2, east),
    ]

    for name, lat, lon in ghosts:
        rows.append({
            "Nom": name,
            "Banniere": "",
            "Adresse": "",
            "Region": region_name,
            "Code_postal": "",
            "Latitude": lat,
            "Longitude": lon,
            "Prix_regulier": "",
            "Prix_super": "",
            "Prix_diesel": "",
            "rang_region": "",
            "highlight_carte": "",
            "is_ghost": "true",
            "date_import": rows[0]["date_import"] if rows else ""
        })


# ------------------------------------------------------------------
# 1️⃣ Collecte par région
# ------------------------------------------------------------------

rows_by_region = defaultdict(list)

date_import = (
    datetime.now(ZoneInfo("America/Montreal"))
    .strftime("%Y-%m-%d %H:%M")
)

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
        "is_ghost": "false",
        "date_import": date_import
    }

    rows_by_region[row["Region"]].append(row)

# ------------------------------------------------------------------
# 2️⃣ Calcul du rang régional
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

# ------------------------------------------------------------------
# 3️⃣ CSV principal
# ------------------------------------------------------------------

write_csv(OUTPUT_MAIN, final_rows)

# ------------------------------------------------------------------
# 4️⃣ CSV régionaux + points fantômes
# ------------------------------------------------------------------

REGIONS_GRAND_MONTREAL = [
    "Montréal", "Laval", "Montérégie", "Laurentides", "Lanaudière"
]

REGIONS_REGION_QUEBEC = [
    "Capitale-Nationale", "Chaudière-Appalaches"
]

rows_grand_montreal = [r for r in final_rows if r["Region"] in REGIONS_GRAND_MONTREAL]
rows_region_quebec = [r for r in final_rows if r["Region"] in REGIONS_REGION_QUEBEC]
rows_mauricie = [r for r in final_rows if r["Region"] == "Mauricie"]
rows_estrie = [r for r in final_rows if r["Region"] == "Estrie"]
rows_sag_lsj = [r for r in final_rows if r["Region"] == "Saguenay-Lac-Saint-Jean"]

add_ghost_points(rows_mauricie, "Mauricie",
                 bbox=(49.0016, 46.1512, -75.5211, -71.8906))

add_ghost_points(rows_estrie, "Estrie",
                 bbox=(46.8000, 45.0000, -72.5000, -70.8000))

add_ghost_points(rows_sag_lsj, "Saguenay-Lac-Saint-Jean",
                 bbox=(49.2000, 47.3000, -74.8000, -70.9000))

add_ghost_points(rows_region_quebec, "Région de Québec",
                 bbox=(47.1200, 45.0000, -72.9000, -69.6000))

write_csv(OUTPUT_GRAND_MONTREAL, rows_grand_montreal)
write_csv(OUTPUT_REGION_QUEBEC, rows_region_quebec)
write_csv(OUTPUT_MAURICIE, rows_mauricie)
write_csv(OUTPUT_ESTRIE, rows_estrie)
write_csv(OUTPUT_SAG_LSJ, rows_sag_lsj)
