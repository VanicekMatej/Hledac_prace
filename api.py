from fastapi import FastAPI, Query
from fastapi.middleware.cors import CORSMiddleware
from typing import Optional
import sqlite3
import math
import httpx

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

def haversine(lat1, lon1, lat2, lon2):
    R = 6371
    dlat = math.radians(lat2 - lat1)
    dlon = math.radians(lon2 - lon1)
    a = math.sin(dlat/2)**2 + math.cos(math.radians(lat1)) * math.cos(math.radians(lat2)) * math.sin(dlon/2)**2
    return R * 2 * math.asin(math.sqrt(a))

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

@app.get("/jobs/mapa")
def jobs_mapa(
    profese:   Optional[str] = Query(None),
    kraj:      Optional[str] = Query(None),
    okres:     Optional[str] = Query(None),
    plat_od:   Optional[int] = Query(None),
    plat_do:   Optional[int] = Query(None),
):
    conn = get_db()

    sql = """
        SELECT j.id, j.profese, j.zamestnavatel, j.plat_od, ob.nazev as obec, ob.lat, ob.lon
        FROM jobs j
        LEFT JOIN obce ob ON j.obec_kod = ob.id
        WHERE ob.lat IS NOT NULL
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

    rows = conn.execute(sql, params).fetchall()
    conn.close()
    return [dict(r) for r in rows]

@app.get("/jobs/dojezd")
async def jobs_dojezd(
    lat:        float = Query(...),
    lon:        float = Query(...),
    vzdalenost: int   = Query(30, description="Maximální vzdálenost v minutách jízdy"),
):
    conn = get_db()

    vsechny_obce = conn.execute("""
        SELECT DISTINCT o.id, o.lat, o.lon
        FROM obce o
        INNER JOIN jobs j ON j.obec_kod = o.id
        WHERE o.lat IS NOT NULL
    """).fetchall()

    blizke_obce = []
    for obec in vsechny_obce:
        d = haversine(lat, lon, obec["lat"], obec["lon"])
        if d <= vzdalenost * 1.5:
            blizke_obce.append((obec["id"], obec["lat"], obec["lon"], d))

    if not blizke_obce:
        conn.close()
        return []

    koordinaty = f"{lon},{lat}"
    for _, o_lat, o_lon, _ in blizke_obce:
        koordinaty += f";{o_lon},{o_lat}"

    try:
        osrm_url = f"http://router.project-osrm.org/table/v1/driving/{koordinaty}"
        osrm_res = httpx.get(osrm_url, params={"sources": "0"}, timeout=15).json()
        durations = osrm_res["durations"][0][1:]
    except Exception:
        durations = [d * 60 for _, _, _, d in blizke_obce]

    max_sekund = vzdalenost * 60
    dobre_obce = []
    for i, (obec_id, _, _, _) in enumerate(blizke_obce):
        if i < len(durations) and durations[i] is not None:
            if durations[i] <= max_sekund:
                dobre_obce.append(obec_id)

    if not dobre_obce:
        conn.close()
        return []

    placeholders = ",".join(["?" for _ in dobre_obce])
    rows = conn.execute(f"""
        SELECT j.id, j.profese, j.zamestnavatel, j.plat_od,
               ob.nazev as obec, ob.lat, ob.lon
        FROM jobs j
        LEFT JOIN obce ob ON j.obec_kod = ob.id
        WHERE j.obec_kod IN ({placeholders})
    """, dobre_obce).fetchall()

    conn.close()
    return [dict(r) for r in rows]

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

@app.get("/autocomplete")
async def autocomplete(q: str = Query(...)):
    try:
        res = httpx.get(
            "https://nominatim.openstreetmap.org/search",
            params={
                "q": q,
                "country": "CZ",
                "format": "json",
                "limit": 5,
                "addressdetails": 1,
            },
            headers={"User-Agent": "hledac-prace-app/1.0"},
            timeout=5
        ).json()

        vysledky = []
        for r in res:
            nazev = r.get("display_name", "").split(",")[0]
            vysledky.append({
                "nazev": nazev,
                "display": r.get("display_name", ""),
                "lat": float(r["lat"]),
                "lon": float(r["lon"]),
            })
        return vysledky
    except Exception:
        return []