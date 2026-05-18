import gzip
import json

print("Načítám data...")

with gzip.open("data/volna-mista.json.gz", "rt", encoding="utf-8") as f:
    data = json.load(f)

polozky = data["polozky"]

print(f"Typ polozky: {type(polozky)}")
print(f"Počet: {len(polozky)}")

# Podívejme se na první položku
prvni = polozky[0]
print(f"\nTyp první položky: {type(prvni)}")
print(json.dumps(prvni, indent=2, ensure_ascii=False))