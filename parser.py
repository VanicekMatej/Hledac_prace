import gzip
import json
import sqlite3

def vytvor_db():
    conn = sqlite3.connect("jobs.db")
    conn.execute("""
        CREATE TABLE IF NOT EXISTS jobs (
            id              TEXT PRIMARY KEY,
            profese         TEXT,
            zamestnavatel   TEXT,
            plat_od         INTEGER,
            plat_do         INTEGER,
            popis           TEXT,
            obec_kod        TEXT,
            okres_kod       TEXT,
            kraj_kod        TEXT,
            datum_vlozeni   TEXT,
            expirace        TEXT,
            url             TEXT,
            kontakt_jmeno   TEXT,
            kontakt_telefon TEXT,
            kontakt_email   TEXT
        )
    """)
    conn.commit()
    return conn

def zpracuj_zaznam(job):
    """Vytáhne důležité hodnoty z jednoho záznamu"""

    # Profese
    profese = None
    if job.get("pozadovanaProfese"):
        profese = job["pozadovanaProfese"].get("cs")

    # Popis
    popis = None
    if job.get("upresnujiciInformace"):
        popis = job["upresnujiciInformace"].get("cs")

    # Lokalita
    obec_kod = okres_kod = kraj_kod = None
    misto = job.get("mistoVykonuPrace") or {}
    if misto:
        if misto.get("obec"):
            obec_kod = misto["obec"].get("id")
        pracoviste = misto.get("pracoviste") or []
        if pracoviste:
            adresa = pracoviste[0].get("adresa") or {}
            if adresa.get("okres"):
                okres_kod = adresa["okres"].get("id")
            if adresa.get("kraj"):
                kraj_kod = adresa["kraj"].get("id")

    # Kontakt
    kontakt_jmeno = kontakt_telefon = kontakt_email = None
    prvni_kontakt = job.get("prvniKontaktSeZamestnavatelem") or {}
    if prvni_kontakt.get("komuSeHlasit"):
        k = prvni_kontakt["komuSeHlasit"]
        jmeno = " ".join(filter(None, [k.get("jmeno"), k.get("prijmeni")]))
        kontakt_jmeno = jmeno or None
        kontakt_telefon = k.get("telefon")
        kontakt_email = k.get("email")

    # Zamestnavatel
    zamestnavatel = None
    if job.get("zamestnavatel"):
        zamestnavatel = job["zamestnavatel"].get("nazev")

    return (
        str(job.get("portalId")),
        profese,
        zamestnavatel,
        job.get("mesicniMzdaOd"),
        job.get("mesicniMzdaDo"),
        popis,
        obec_kod,
        okres_kod,
        kraj_kod,
        job.get("datumVlozeni"),
        job.get("expirace"),
        job.get("urlAdresa"),
        kontakt_jmeno,
        kontakt_telefon,
        kontakt_email,
    )

print("Připravuji databázi...")
conn = vytvor_db()

print("Načítám a ukládám data...")
with gzip.open("data/volna-mista.json.gz", "rt", encoding="utf-8") as f:
    data = json.load(f)

polozky = data["polozky"]
print(f"Celkem záznamů: {len(polozky)}")

pocet = 0
for job in polozky:
    zaznam = zpracuj_zaznam(job)
    conn.execute("""
        INSERT OR REPLACE INTO jobs VALUES
        (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)
    """, zaznam)
    pocet += 1

    if pocet % 5000 == 0:
        conn.commit()
        print(f"  Uloženo {pocet} / {len(polozky)}...")

conn.commit()
conn.close()
print(f"\nHotovo! {pocet} pracovních míst uloženo do jobs.db")