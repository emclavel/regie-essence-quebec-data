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
# Lecture du GeoJSON (gzip ou non)
# ------------------------------------------------------------------

if raw.lstrip().startswith(b"{"):
    data = json.loads(raw.decode("utf-8"))
else:
    with gzip.open(BytesIO(raw), "rt", encoding="utf-8") as f:
        data = json.load(f)

features = data.get("features", [])
print(f"Stations détectées : {len(features)}")

# ------------------------------------------------------------------
# Utilitaires
# ------------------------------------------------------------------

def extract_prices(prices_list):
    prix_regulier = prix_super = prix_diesel = None

    for item in prices_list:
        if not item.get("IsAvailable"):
            continue
        try:
            price = float(item["Price"].replace("¢", "").strip())
        except Exception:
            continue

        if item["GasType"] == "Régulier":
            prix_regulier = price
        elif item["GasType"] == "Super":
            prix_super = price
        elif item["GasType"] == "Diesel":
            prix_diesel = price

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
            "is_ghost": 0,
            "date_import": rows[0]["date_import"] if rows else ""
        })

# ------------------------------------------------------------------
# Collecte des données
# ------------------------------------------------------------------

rows_by_region = defaultdict(list)

date_import = datetime.now(
    ZoneInfo("America/Montreal")
).strftime("%Y-%m-%d %H:%M")

for feature in features:
    props = feature.get("properties", {})
    lon, lat = feature.get("geometry", {}).get("coordinates", [None, None])

    prix_regulier, prix_super, prix_diesel = extract_prices(
        props.get("Prices", [])
    )

    if prix_regulier is None:
        continue

    rows_by_region[props.get("Region")].append({
        "Nom": props.get("Name"),
        "Banniere": props.get("brand"),
        "Adresse": props.get("Address"),
        "Region": props.get("Region"),
        "Code_postal": props.get("PostalCode"),
        "Latitude": lat,
        "Longitude": lon,
        "Prix_regulier": prix_regulier,
        "Prix_super": prix_super,
        "Prix_diesel": prix_diesel,
        "rang_region": None,
        "highlight_carte": "",
        "is_ghost": 1,
        "date_import": date_import
    })

# ------------------------------------------------------------------
# Classement régional
# ------------------------------------------------------------------

final_rows = []

for region, rows in rows_by_region.items():
    rows_sorted = sorted(rows, key=lambda r: r["Prix_regulier"])
    rank = 0
    last_price = None

    for idx, row in enumerate(rows_sorted):
        if row["Prix_regulier"] != last_price:
            rank = idx + 1
            last_price = row["Prix_regulier"]
        row["rang_region"] = rank
        row["highlight_carte"] = "oui" if rank == 1 else ""

    final_rows.extend(rows_sorted[:5])

# ------------------------------------------------------------------
# CSV principal
# ------------------------------------------------------------------

write_csv(OUTPUT_MAIN, final_rows)

# ------------------------------------------------------------------
# CSV régionaux + points fantômes
# ------------------------------------------------------------------

rows_grand_montreal = [r for r in final_rows if r["Region"] in [
    "Montréal", "Laval", "Montérégie", "Laurentides", "Lanaudière"
]]

rows_region_quebec = [r for r in final_rows if r["Region"] in [
    "Capitale-Nationale", "Chaudière-Appalaches"
]]

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
