import requests
import sqlite3
import time

conn = sqlite3.connect("jobs.db")

try:
    conn.execute("ALTER TABLE obce ADD COLUMN lat REAL")
    conn.execute("ALTER TABLE obce ADD COLUMN lon REAL")
    conn.commit()
except:
    pass

obce = conn.execute("""
    SELECT DISTINCT o.id, o.nazev 
    FROM obce o
    INNER JOIN jobs j ON j.obec_kod = o.id
    WHERE o.lat IS NULL
""").fetchall()

print(f"Obcí použitých v pracovních místech: {len(obce)}")

nalezeno = 0
chyba = 0

for i, (obec_id, nazev) in enumerate(obce):
    try:
        res = requests.get(
            "https://nominatim.openstreetmap.org/search",
            params={
                "city": nazev,
                "country": "CZ",
                "format": "json",
                "limit": 1
            },
            headers={"User-Agent": "hledac-prace-app/1.0"},
            timeout=10
        ).json()

        if res:
            lat = float(res[0]["lat"])
            lon = float(res[0]["lon"])
            conn.execute("UPDATE obce SET lat=?, lon=? WHERE id=?", (lat, lon, obec_id))
            nalezeno += 1
        else:
            chyba += 1

        if i % 50 == 0:
            conn.commit()
            print(f"  {i}/{len(obce)} — nalezeno: {nalezeno}, nenalezeno: {chyba}")

        time.sleep(1)

    except Exception as e:
        chyba += 1
        print(f"  Chyba u {nazev}: {e}")

conn.commit()
conn.close()
print(f"\nHotovo! Nalezeno: {nalezeno}, nenalezeno: {chyba}")