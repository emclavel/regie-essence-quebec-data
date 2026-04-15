import os
import requests
import pandas as pd
from io import BytesIO

# URL officielle du fichier Excel téléchargé sur le site de la Régie
URL = "https://regieessencequebec.ca/data/stations.xlsx"

# Chemin de sortie du CSV pour Datawrapper
OUTPUT_PATH = "data/regie_essence_quebec.csv"

# S'assurer que le dossier data existe
os.makedirs("data", exist_ok=True)

# En-têtes HTTP pour éviter le blocage 403 (anti-bot)
headers = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                  "AppleWebKit/537.36 (KHTML, like Gecko) "
                  "Chrome/123.0 Safari/537.36",
    "Accept": "*/*",
    "Referer": "https://regieessencequebec.ca/"
}

# Télécharger le fichier Excel
response = requests.get(URL, headers=headers, timeout=60)
response.raise_for_status()

# Lire l'Excel en mémoire
df = pd.read_excel(BytesIO(response.content))

# Renommer les colonnes pour un CSV propre et stable
df = df.rename(columns={
    "Nom": "Nom",
    "Bannière": "Bannière",
    "Adresse": "Adresse",
    "Région": "Région",
    "Code Postal": "Code_postal",
    "Latitude": "Latitude",
    "Longitude": "Longitude",
    "Prix Régulier": "Prix_regulier",
    "Prix Super": "Prix_super",
    "Prix Diesel": "Prix_diesel"
})

# Nettoyer les prix : enlever ¢, transformer en float, gérer N/D
def clean_price(value):
    if isinstance(value, str):
        value = value.replace("¢", "").strip()
        if value.upper() == "N/D":
            return None
    try:
        return float(value)
    except Exception:
        return None

for col in ["Prix_regulier", "Prix_super", "Prix_diesel"]:
    if col in df.columns:
        df[col] = df[col].apply(clean_price)

# Exporter en CSV (source finale pour Datawrapper)
df.to_csv(OUTPUT_PATH, index=False, encoding="utf-8")
