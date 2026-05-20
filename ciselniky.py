import requests
import sqlite3

CISELNIKY = {
    "kraje":  "https://data.mpsv.cz/od/soubory/ciselniky/kraje.json",
    "okresy": "https://data.mpsv.cz/od/soubory/ciselniky/okresy.json",
    "obce":   "https://data.mpsv.cz/od/soubory/ciselniky/obce.json",
}

def vytvor_tabulky(conn):
    conn.execute("""
        CREATE TABLE IF NOT EXISTS kraje (
            id    TEXT PRIMARY KEY,
            nazev TEXT
        )
    """)
    conn.execute("""
        CREATE TABLE IF NOT EXISTS okresy (
            id      TEXT PRIMARY KEY,
            nazev   TEXT,
            kraj_id TEXT
        )
    """)
    conn.execute("""
        CREATE TABLE IF NOT EXISTS obce (
            id       TEXT PRIMARY KEY,
            nazev    TEXT,
            okres_id TEXT,
            kraj_id  TEXT
        )
    """)
    conn.commit()

conn = sqlite3.connect("jobs.db")
vytvor_tabulky(conn)

# Kraje
print("Stahuji kraje...")
data = requests.get(CISELNIKY["kraje"]).json()
for p in data["polozky"]:
    conn.execute("INSERT OR REPLACE INTO kraje VALUES (?, ?)", (
        p["id"],
        p["nazev"]["cs"]
    ))
conn.commit()
print(f"  Uloženo {len(data['polozky'])} krajů")

# Okresy
print("Stahuji okresy...")
data = requests.get(CISELNIKY["okresy"]).json()
for p in data["polozky"]:
    kraj_id = p.get("kraj")
    conn.execute("INSERT OR REPLACE INTO okresy VALUES (?, ?, ?)", (
        p["id"],
        p["nazev"]["cs"],
        kraj_id
    ))
conn.commit()
print(f"  Uloženo {len(data['polozky'])} okresů")

# Obce
print("Stahuji obce... (může chvíli trvat)")
data = requests.get(CISELNIKY["obce"]).json()
for p in data["polozky"]:
    okres_id = p.get("okres") if isinstance(p.get("okres"), str) else None
    kraj_id  = p.get("kraj")  if isinstance(p.get("kraj"),  str) else None
    conn.execute("INSERT OR REPLACE INTO obce VALUES (?, ?, ?, ?)", (
        p["id"],
        p["nazev"]["cs"],
        okres_id,
        kraj_id
    ))
conn.commit()
print(f"  Uloženo {len(data['polozky'])} obcí")

conn.close()
print("\nHotovo! Číselníky uloženy do jobs.db")