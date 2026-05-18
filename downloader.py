import urllib.request
import os

URL = "https://data.mpsv.cz/od/soubory/volna-mista/volna-mista.json.gz"
SOUBOR = "data/volna-mista.json.gz"

# Vytvoří složku data/ pokud neexistuje
os.makedirs("data", exist_ok=True)

print("Stahuji data z MPSV...")
urllib.request.urlretrieve(URL, SOUBOR)
print(f"Hotovo! Soubor uložen do {SOUBOR}")