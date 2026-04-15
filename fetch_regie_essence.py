import requests
import json
import gzip
from io import BytesIO

URL = "https://regieessencequebec.ca/stations.geojson.gz"

headers = {
    "User-Agent": "Mozilla/5.0",
    "Accept": "*/*"
}

response = requests.get(URL, headers=headers, timeout=60)
response.raise_for_status()
raw = response.content

# Détecter si le JSON est gzip ou non
if raw.lstrip().startswith(b"{"):
    data = json.loads(raw.decode("utf-8"))
else:
    with gzip.open(BytesIO(raw), "rt", encoding="utf-8") as f:
        data = json.load(f)

features = data.get("features", [])
print(f"Nombre de stations: {len(features)}")

# Inspecter UNE station (la première)
first = features[0]

print("\n=== KEYS AU NIVEAU feature ===")
print(first.keys())

props = first.get("properties", {})
print("\n=== KEYS AU NIVEAU properties ===")
print(props.keys())

print("\n=== CONTENU COMPLET DE properties (extrait) ===")
print(json.dumps(props, indent=2)[:2000])
