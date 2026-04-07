#!/usr/bin/env python3
"""
iRacing History Importer
Importa tu historial completo de carreras e iRating desde la API de iRacing.

Requisitos: pip install iracingdataapi
Uso:        python import_history.py
"""

import os
import sqlite3
import time
from pathlib import Path
from datetime import date, datetime
from dotenv import load_dotenv

load_dotenv()

DB_PATH = Path(__file__).parent / "iracing_data.db"

CATEGORY_ROAD      = 2
CATEGORY_OVAL      = 1
CATEGORY_DIRT_ROAD = 3
CATEGORY_DIRT_OVAL = 4

EVENT_RACE    = 5
EVENT_QUALIFY = 4
EVENT_PRACTICE= 3


# ─── Auto-install ─────────────────────────────────────────────────────────────
def get_client():
    try:
        from iracingdataapi.client import irDataClient
        return irDataClient
    except (ImportError, ModuleNotFoundError):
        import subprocess, sys
        print("📦 Instalando dependencias (iracingdataapi + pydantic)...")
        subprocess.check_call([sys.executable, "-m", "pip", "install",
                               "iracingdataapi", "pydantic", "-q"])
        from iracingdataapi.client import irDataClient
        return irDataClient


# ─── Helpers ──────────────────────────────────────────────────────────────────
def ir_time(val):
    """iRacing guarda tiempos en 1/10000 de segundo."""
    if val and val > 0:
        return val / 10000.0
    return None

def sr_float(val):
    """iRacing guarda el SR como entero × 100 (ej. 350 = 3.50)."""
    if val is not None:
        return val / 100.0
    return None

def normalize_results(raw):
    """Normaliza la respuesta de la API (puede ser lista o dict con 'results')."""
    if raw is None:
        return []
    if isinstance(raw, list):
        return raw
    if isinstance(raw, dict):
        return raw.get("results", [])
    return []


# ─── Import ───────────────────────────────────────────────────────────────────
def import_races(client, cursor, conn, cust_id, category_id, label):
    today           = date.today()
    current_year    = today.year
    current_quarter = (today.month - 1) // 3 + 1

    imported = 0
    skipped  = 0
    errors   = 0

    print(f"\n🏁 Buscando historial {label} (últimos 3 años)...")

    for year in range(current_year - 2, current_year + 1):
        for quarter in range(1, 5):
            if year == current_year and quarter > current_quarter:
                break

            try:
                raw = client.result_search_series(
                    season_year=year,
                    season_quarter=quarter,
                    cust_id=cust_id,
                    category_ids=[category_id],
                    event_types=[EVENT_RACE],
                )
                races = normalize_results(raw)

                if not races:
                    continue

                print(f"   {year} Q{quarter}: {len(races)} carreras", end="")

                q_imported = 0
                for race in races:
                    sub_id = race.get("subsession_id")
                    if not sub_id:
                        continue

                    # ¿Ya existe?
                    if cursor.execute(
                        "SELECT id FROM sessions WHERE subsession_id = ?",
                        (sub_id,)
                    ).fetchone():
                        skipped += 1
                        continue

                    # iRating y SR
                    ir_b = race.get("oldi_rating")
                    ir_a = race.get("newi_rating")
                    ir_c = (ir_a - ir_b) if (ir_b and ir_a) else None

                    sr_b_raw = race.get("old_sub_level")
                    sr_a_raw = race.get("new_sub_level")
                    sr_b = sr_float(sr_b_raw) if sr_b_raw else None
                    sr_a = sr_float(sr_a_raw) if sr_a_raw else None
                    sr_c = round(sr_a - sr_b, 3) if (sr_a and sr_b) else None

                    # Track
                    track = race.get("track", {}) or {}
                    track_name   = track.get("track_name")   or race.get("track_name", "Unknown")
                    track_config = track.get("config_name")  or ""

                    # Posición (0-indexed en la API)
                    finish = race.get("finish_position_in_class")
                    if finish is None:
                        finish = race.get("finish_position")
                    if finish is not None:
                        finish += 1

                    start = race.get("starting_position_in_class")
                    if start is None:
                        start = race.get("starting_position")
                    if start is not None:
                        start += 1

                    cursor.execute("""
                        INSERT INTO sessions (
                            session_date, subsession_id,
                            track_name, track_config,
                            car_name, car_id,
                            session_type, series_name, sof,
                            start_position, finish_position,
                            total_laps, total_incidents,
                            best_lap_time, avg_lap_time,
                            irating_before, irating_after, irating_change,
                            sr_before, sr_after, sr_change,
                            champ_points
                        ) VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)
                    """, (
                        race.get("start_time", ""),
                        sub_id,
                        track_name,
                        track_config,
                        race.get("car_name", "Unknown"),
                        race.get("car_id"),
                        "Race",
                        race.get("series_name", ""),
                        race.get("event_strength_of_field"),
                        start,
                        finish,
                        race.get("laps_complete", 0),
                        race.get("incidents", 0),
                        ir_time(race.get("best_lap_time")),
                        ir_time(race.get("average_lap")),
                        ir_b, ir_a, ir_c,
                        sr_b, sr_a, sr_c,
                        race.get("champ_pts", 0),
                    ))
                    imported  += 1
                    q_imported += 1

                conn.commit()
                print(f"  →  {q_imported} nuevas")
                time.sleep(0.4)   # Rate limiting

            except Exception as e:
                errors += 1
                err_msg = str(e)
                # Respuesta vacía = fallo de autenticación (ej: 2FA activo)
                if "Expecting value" in err_msg or "line 1 column 1" in err_msg:
                    print(f"\n   ❌ La API devuelve respuestas vacías — esto indica un fallo de autenticación.")
                    print(f"      Causa más común: tienes el 2FA (verificación en dos pasos) activado.")
                    print(f"      Solución: desactívalo en members.iracing.com → My Account → Security")
                    return 0, 0, errors
                print(f"\n   ⚠️  {year} Q{quarter}: {e}")

    return imported, skipped, errors


def update_driver_profile(client, cursor, conn, cust_id):
    """Guarda el perfil actual del piloto (iRating, SR, licencia, etc.)."""
    try:
        # Obtener el iRating/SR más reciente de las sesiones importadas
        latest = cursor.execute("""
            SELECT irating_after, sr_after
            FROM sessions
            WHERE irating_after IS NOT NULL
            ORDER BY session_date DESC LIMIT 1
        """).fetchone()

        if latest:
            # Intentar obtener nombre de la API
            display_name = "Piloto"
            try:
                info = client.member_info()
                if info:
                    display_name = info.get("display_name", "Piloto")
            except Exception:
                pass

            cursor.execute("""
                INSERT INTO driver_profile (
                    cust_id, display_name, irating_road, sr_road
                ) VALUES (?, ?, ?, ?)
            """, (cust_id, display_name, latest[0], latest[1]))
            conn.commit()
            print(f"\n👤 Perfil actualizado: iRating {latest[0]}"
                  + (f"  SR {latest[1]:.2f}" if latest[1] else ""))

    except Exception as e:
        print(f"\n⚠️  No se pudo actualizar el perfil: {e}")


def print_summary(cursor):
    """Muestra un resumen de los datos en la BD."""
    total   = cursor.execute("SELECT COUNT(*) FROM sessions WHERE session_type='Race'").fetchone()[0]
    with_ir = cursor.execute("SELECT COUNT(*) FROM sessions WHERE irating_change IS NOT NULL").fetchone()[0]
    best    = cursor.execute(
        "SELECT MAX(irating_after) FROM sessions WHERE irating_after IS NOT NULL"
    ).fetchone()[0]
    worst   = cursor.execute(
        "SELECT MIN(irating_after) FROM sessions WHERE irating_after IS NOT NULL"
    ).fetchone()[0]
    changes = cursor.execute(
        "SELECT SUM(irating_change) FROM sessions WHERE irating_change IS NOT NULL"
    ).fetchone()[0]

    print("\n" + "═" * 50)
    print("📊 RESUMEN DE TU HISTORIAL")
    print("═" * 50)
    print(f"   Carreras totales:      {total}")
    print(f"   Con datos de iRating:  {with_ir}")
    if best:
        print(f"   iRating máximo:        {best}")
    if worst and best:
        print(f"   iRating mínimo:        {worst}")
    if changes is not None:
        print(f"   Cambio total iRating:  {changes:+d}")
    print("═" * 50)
    print("\n🏁 ¡Ejecuta el dashboard para ver todo!")
    print("   python dashboard.py")


# ─── Main ─────────────────────────────────────────────────────────────────────
def main():
    email    = os.getenv("IRACING_EMAIL")
    password = os.getenv("IRACING_PASSWORD")
    cust_id  = os.getenv("IRACING_CUST_ID")

    if not email or not password or not cust_id:
        print("❌  Configura IRACING_EMAIL, IRACING_PASSWORD y IRACING_CUST_ID en el archivo .env")
        print()
        print("Ejemplo .env:")
        print("   IRACING_EMAIL=tu@email.com")
        print("   IRACING_PASSWORD=tucontraseña")
        print("   IRACING_CUST_ID=123456")
        return

    cust_id = int(cust_id)

    irDataClient = get_client()

    print("\n🔐 Conectando a iRacing API...")
    try:
        client = irDataClient(username=email, password=password, use_pydantic=False)
        print("   ✅ Cliente creado — probando con la primera búsqueda...")
    except Exception as e:
        print(f"   ❌ Error al crear cliente: {e}")
        return

    conn   = sqlite3.connect(str(DB_PATH))
    cursor = conn.cursor()

    # Importar Road
    imp_r, skip_r, err_r = import_races(
        client, cursor, conn, cust_id, CATEGORY_ROAD, "Road (GT3, LMP, F1…)"
    )

    # Preguntar si también importar Oval
    total_road = imp_r + skip_r
    print(f"\n{'─'*50}")
    print(f"Road:  {imp_r} nuevas  |  {skip_r} ya existían  |  {err_r} errores")

    if total_road > 0 or imp_r > 0:
        try:
            resp = input("\n¿Importar también carreras de Oval? (s/N): ").strip().lower()
            if resp in ("s", "si", "sí", "y", "yes"):
                imp_o, skip_o, err_o = import_races(
                    client, cursor, conn, cust_id, CATEGORY_OVAL, "Oval"
                )
                imp_r  += imp_o
                skip_r += skip_o
                print(f"Oval:  {imp_o} nuevas  |  {skip_o} ya existían")
        except (KeyboardInterrupt, EOFError):
            pass

    if imp_r > 0:
        update_driver_profile(client, cursor, conn, cust_id)

    print_summary(cursor)
    conn.close()


if __name__ == "__main__":
    main()
