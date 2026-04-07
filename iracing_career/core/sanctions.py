"""
Sistema de sanciones: reposo médico, suspensiones disciplinarias.
"""
from datetime import datetime, timedelta

# Umbrales que disparan sanciones automáticas
WEEKLY_INCIDENT_LIMIT = 10       # puntos/semana → 3 días de reposo
SERIOUS_ACCIDENT_LIMIT = 3       # accidentes graves/mes → alerta
SERIOUS_ACCIDENT_THRESHOLD = 4   # incidentes en una carrera = "grave"


def evaluate_sanctions(recent_races: list[dict]) -> list[dict]:
    """
    Analiza carreras recientes y genera sanciones si procede.
    Devuelve lista de sanciones nuevas a aplicar.
    """
    new_sanctions = []

    # Carreras de la última semana
    week_ago = datetime.utcnow() - timedelta(days=7)
    week_races = [
        r for r in recent_races
        if _parse_date(r.get("raced_at", "")) > week_ago
    ]
    weekly_incidents = sum(r["incidents"] for r in week_races)

    if weekly_incidents >= WEEKLY_INCIDENT_LIMIT:
        new_sanctions.append({
            "type": "disciplinary",
            "reason": f"Superado el límite semanal de incidentes ({weekly_incidents}x)",
            "days_rest": 3,
            "races_banned": 0,
        })

    # Accidentes graves este mes
    month_ago = datetime.utcnow() - timedelta(days=30)
    month_races = [
        r for r in recent_races
        if _parse_date(r.get("raced_at", "")) > month_ago
    ]
    serious = [r for r in month_races if r["incidents"] >= SERIOUS_ACCIDENT_THRESHOLD]

    if len(serious) >= SERIOUS_ACCIDENT_LIMIT:
        new_sanctions.append({
            "type": "medical",
            "reason": f"{len(serious)} accidentes graves este mes. Reposo médico obligatorio.",
            "days_rest": 7,
            "races_banned": 0,
        })

    return new_sanctions


def is_pilot_banned(sanctions: list[dict]) -> tuple[bool, str]:
    """
    Comprueba si hay sanciones activas que impidan correr.
    Devuelve (banned, motivo).
    """
    for s in sanctions:
        if s.get("active") and (s.get("days_rest", 0) > 0 or s.get("races_banned", 0) > 0):
            return True, s.get("reason", "Sanción activa")
    return False, ""


def sanction_ends_at(days_rest: int) -> str:
    return (datetime.utcnow() + timedelta(days=days_rest)).isoformat()


def _parse_date(date_str: str) -> datetime:
    try:
        return datetime.fromisoformat(date_str.replace("Z", ""))
    except Exception:
        return datetime.min
