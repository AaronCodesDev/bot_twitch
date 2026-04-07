"""
Equipos disponibles, generación de ofertas y validación de contratos.
"""

TEAMS = [
    {
        "id": "apex",
        "name": "Apex Motorsport",
        "salary_per_race": 8500,
        "min_sr": 4.5,
        "min_irating": 3500,
        "min_wins": 5,
        "max_incidents_per_race": 4,
        "tier": 2,
        "description": "Equipo sólido de Clase A. Exige limpieza.",
    },
    {
        "id": "redline",
        "name": "Redline Racing",
        "salary_per_race": 12000,
        "min_sr": 4.0,
        "min_irating": 4500,
        "min_wins": 10,
        "max_incidents_per_race": 3,
        "tier": 1,
        "description": "Equipo de élite. Solo para los mejores.",
    },
    {
        "id": "velocity",
        "name": "Velocity GT",
        "salary_per_race": 4500,
        "min_sr": 3.5,
        "min_irating": 2000,
        "min_wins": 2,
        "max_incidents_per_race": 6,
        "tier": 3,
        "description": "Equipo en crecimiento. Buena puerta de entrada.",
    },
    {
        "id": "ironwall",
        "name": "Ironwall Endurance",
        "salary_per_race": 6000,
        "min_sr": 4.0,
        "min_irating": 2800,
        "min_wins": 3,
        "max_incidents_per_race": 5,
        "tier": 2,
        "description": "Especialistas en resistencia. Valoran la consistencia.",
    },
]


def get_available_offers(irating: int, sr: float, wins: int) -> list[dict]:
    """Devuelve equipos que ofrecen contrato según las stats del piloto."""
    offers = []
    for team in TEAMS:
        reqs = check_requirements(team, irating, sr, wins)
        offers.append({**team, "requirements_check": reqs})
    return sorted(offers, key=lambda t: t["tier"])


def check_requirements(team: dict, irating: int, sr: float, wins: int) -> dict:
    """Comprueba cada requisito individualmente."""
    return {
        "sr": {"ok": sr >= team["min_sr"], "current": sr, "needed": team["min_sr"]},
        "irating": {"ok": irating >= team["min_irating"], "current": irating, "needed": team["min_irating"]},
        "wins": {"ok": wins >= team["min_wins"], "current": wins, "needed": team["min_wins"]},
    }


def all_requirements_met(team: dict, irating: int, sr: float, wins: int) -> bool:
    reqs = check_requirements(team, irating, sr, wins)
    return all(v["ok"] for v in reqs.values())


def evaluate_contract_performance(contract: dict, recent_races: list[dict]) -> dict:
    """
    Evalúa si el piloto está cumpliendo con su contrato actual.
    Devuelve estado y si procede despido.
    """
    if not recent_races:
        return {"status": "ok", "fire": False, "reason": ""}

    avg_incidents = sum(r["incidents"] for r in recent_races) / len(recent_races)
    recent_srs = [r.get("sr_change", 0) for r in recent_races]
    sr_trend = sum(recent_srs)

    warnings = []
    fire = False

    if avg_incidents > contract["max_incidents_per_race"]:
        warnings.append(f"Incidentes medios ({avg_incidents:.1f}) superan el límite ({contract['max_incidents_per_race']})")
        if avg_incidents > contract["max_incidents_per_race"] * 1.5:
            fire = True

    if sr_trend < -0.5:
        warnings.append("SR cayendo de forma consistente")

    return {
        "status": "warning" if warnings else "ok",
        "fire": fire,
        "warnings": warnings,
    }
