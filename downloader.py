import urllib.request
import os

URL = "https://data.mpsv.cz/od/soubory/volna-mista/volna-mista.json.gz"
SOUBOR = "data/volna-mista.json.gz"

os.makedirs("data", exist_ok=True)

print("Stahuji data")
urllib.request.urlretrieve(URL, SOUBOR)
print(f"Soubor uložen do {SOUBOR}")