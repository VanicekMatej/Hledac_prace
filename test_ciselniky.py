import sqlite3

conn = sqlite3.connect("jobs.db")

# Ukázka jobs s přeloženými názvy
print("Ukázka 10 pracovních míst s názvy krajů a okresů:")
vysledky = conn.execute("""
    SELECT 
        j.profese,
        j.zamestnavatel,
        j.plat_od,
        k.nazev as kraj,
        o.nazev as okres
    FROM jobs j
    LEFT JOIN kraje k ON j.kraj_kod = k.id
    LEFT JOIN okresy o ON j.okres_kod = o.id
    WHERE j.profese IS NOT NULL
    LIMIT 10
""").fetchall()

for r in vysledky:
    print(f"  {r[0]} | {r[1]} | {r[2]} Kč | {r[3]} | {r[4]}")

# Kolik míst má přeložený kraj?
s_krajem = conn.execute("""
    SELECT COUNT(*) FROM jobs j
    JOIN kraje k ON j.kraj_kod = k.id
""").fetchone()[0]

celkem = conn.execute("SELECT COUNT(*) FROM jobs").fetchone()[0]
print(f"\nMísta s přeloženým krajem: {s_krajem} z {celkem}")

conn.close()