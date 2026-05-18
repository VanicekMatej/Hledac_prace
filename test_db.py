import sqlite3

conn = sqlite3.connect("jobs.db")

# Celkový počet
pocet = conn.execute("SELECT COUNT(*) FROM jobs").fetchone()[0]
print(f"Celkem míst v databázi: {pocet}")

# Ukázka 5 záznamů
print("\n5 náhodných záznamů:")
zaznamy = conn.execute("""
    SELECT profese, zamestnavatel, plat_od, plat_do, okres_kod
    FROM jobs
    WHERE profese IS NOT NULL
    LIMIT 5
""").fetchall()

for z in zaznamy:
    print(f"  {z[0]} | {z[1]} | {z[2]}-{z[3]} Kč | {z[4]}")

# Kolik má vyplněný plat?
s_platem = conn.execute("SELECT COUNT(*) FROM jobs WHERE plat_od IS NOT NULL").fetchone()[0]
print(f"\nMísta s vyplněným platem: {s_platem} ({round(s_platem/pocet*100)}%)")

# Top 10 krajů
print("\nPočet míst podle kraje:")
kraje = conn.execute("""
    SELECT kraj_kod, COUNT(*) as pocet
    FROM jobs
    WHERE kraj_kod IS NOT NULL
    GROUP BY kraj_kod
    ORDER BY pocet DESC
    LIMIT 10
""").fetchall()

for k in kraje:
    print(f"  {k[0]}: {k[1]} míst")

conn.close()