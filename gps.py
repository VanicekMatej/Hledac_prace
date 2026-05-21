import requests
import sqlite3
import time



conn = sqlite3.connect("jobs.db")

# Načteme POUZE obce které ještě nemají GPS
obce = conn.execute("""
    SELECT o.id, o.nazev, k.nazev as kraj_nazev
    FROM obce o
    INNER JOIN jobs j ON j.obec_kod = o.id
    LEFT JOIN kraje k ON o.kraj_id = k.id
    WHERE o.lat IS NULL
    GROUP BY o.id
""").fetchall()

print(f"Zbývá obcí k geokódování: {len(obce)}")

nalezeno = 0
chyba = 0

for i, (obec_id, nazev, kraj_nazev) in enumerate(obce):
    try:
        params = {
            "city": nazev,
            "country": "CZ",
            "format": "json",
            "limit": 5,
        }
        if kraj_nazev:
            params["state"] = kraj_nazev

        raw = requests.get(
            "https://nominatim.openstreetmap.org/search",
            params=params,
            headers={"User-Agent": "hledac-prace-app/1.0"},
            timeout=10
        )

        if raw.status_code == 429:
            print(f"  Rate limit! Čekám 60s...")
            time.sleep(60)
            continue

        if not raw.text.strip() or raw.status_code != 200:
            chyba += 1
            continue

        res = raw.json()

        if res:
            lat = float(res[0]["lat"])
            lon = float(res[0]["lon"])
            conn.execute("UPDATE obce SET lat=?, lon=? WHERE id=?", (lat, lon, obec_id))
            nalezeno += 1
        else:
            chyba += 1

        if i % 10 == 0:
            conn.commit()
            print(f"  {i}/{len(obce)} — nalezeno: {nalezeno}, nenalezeno: {chyba}")

        time.sleep(1.5)

    except Exception as e:
        chyba += 1
        print(f"  Chyba u {nazev}: {e}")
        time.sleep(5)

conn.commit()
conn.close()
print(f"\nHotovo! Nalezeno: {nalezeno}, nenalezeno: {chyba}")