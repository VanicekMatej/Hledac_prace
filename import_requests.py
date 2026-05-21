import requests

params = {
    "city": "Praha",
    "country": "CZ",
    "format": "json",
    "limit": 1,
}

raw = requests.get(
    "https://nominatim.openstreetmap.org/search",
    params=params,
    headers={"User-Agent": "hledac-prace-app/1.0"},
    timeout=10
)

print(f"Status: {raw.status_code}")
print(f"Headers: {dict(raw.headers)}")
print(f"Text: '{raw.text[:500]}'")