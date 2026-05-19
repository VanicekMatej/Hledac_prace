from fastapi import FastAPI, Query
from fastapi.middleware.cors import CORSMiddleware
from typing import Optional
import sqlite3

app = FastAPI(title="Hledač práce API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
    allow_methods=["*"],
    allow_headers=["*"],
)

def get_db():
    conn = sqlite3.connect("jobs.db")
    conn.row_factory = sqlite3.Row
    return conn

@app.get("/jobs")
def seznam_jobu(
    profese:   Optional[str] = Query(None),
    kraj:      Optional[str] = Query(None),
    okres:     Optional[str] = Query(None),
    plat_od:   Optional[int] = Query(None),
    plat_do:   Optional[int] = Query(None),
    stranka:   int           = Query(1),
):
    conn = get_db()

    sql = """
        SELECT
            j.id,
            j.profese,
            j.zamestnavatel,
            j.plat_od,
            j.plat_do,
            j.popis,
            j.kontakt_jmeno,
            j.kontakt_telefon,
            j.kontakt_email,
            j.datum_vlozeni,
            k.nazev as kraj,
            o.nazev as okres,
            ob.nazev as obec,
            ob.lat,
            ob.lon
        FROM jobs j
        LEFT JOIN kraje  k  ON j.kraj_kod  = k.id
        LEFT JOIN okresy o  ON j.okres_kod = o.id
        LEFT JOIN obce   ob ON j.obec_kod  = ob.id
        WHERE 1=1
    """
    params = []

    if profese:
        sql += " AND j.profese LIKE ?"
        params.append(f"%{profese}%")
    if kraj:
        sql += " AND j.kraj_kod = ?"
        params.append(kraj)
    if okres:
        sql += " AND j.okres_kod = ?"
        params.append(okres)
    if plat_od:
        sql += " AND j.plat_od >= ?"
        params.append(plat_od)
    if plat_do:
        sql += " AND j.plat_do <= ?"
        params.append(plat_do)

    pocet_sql = f"SELECT COUNT(*) FROM ({sql})"
    celkem = conn.execute(pocet_sql, params).fetchone()[0]

    limit = 20
    offset = (stranka - 1) * limit
    sql += f" ORDER BY j.datum_vlozeni DESC LIMIT {limit} OFFSET {offset}"

    rows = conn.execute(sql, params).fetchall()
    conn.close()

    return {
        "celkem": celkem,
        "stranka": stranka,
        "stranek": (celkem + limit - 1) // limit,
        "vysledky": [dict(r) for r in rows]
    }

@app.get("/jobs/{job_id}")
def detail_jobu(job_id: str):
    conn = get_db()
    row = conn.execute("""
        SELECT j.*, k.nazev as kraj_nazev, o.nazev as okres_nazev,
               ob.nazev as obec_nazev, ob.lat, ob.lon
        FROM jobs j
        LEFT JOIN kraje  k  ON j.kraj_kod  = k.id
        LEFT JOIN okresy o  ON j.okres_kod = o.id
        LEFT JOIN obce   ob ON j.obec_kod  = ob.id
        WHERE j.id = ?
    """, (job_id,)).fetchone()
    conn.close()
    if not row:
        return {"chyba": "Pracovní místo nenalezeno"}
    return dict(row)

@app.get("/kraje")
def seznam_kraju():
    conn = get_db()
    rows = conn.execute("SELECT id, nazev FROM kraje ORDER BY nazev").fetchall()
    conn.close()
    return [dict(r) for r in rows]

@app.get("/okresy")
def seznam_okresu(kraj: Optional[str] = Query(None)):
    conn = get_db()
    if kraj:
        rows = conn.execute(
            "SELECT id, nazev FROM okresy WHERE kraj_id = ? ORDER BY nazev", (kraj,)
        ).fetchall()
    else:
        rows = conn.execute("SELECT id, nazev FROM okresy ORDER BY nazev").fetchall()
    conn.close()
    return [dict(r) for r in rows]