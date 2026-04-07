"""
Lógica económica: premios por posición, penalizaciones, bonificaciones.
"""

# Premio base según posición (1º a 20º)
PRIZE_TABLE = {
    1: 1800, 2: 900, 3: 600, 4: 400, 5: 300,
    6: 220, 7: 180, 8: 140, 9: 110, 10: 90,
}
DEFAULT_PRIZE = 50  # posiciones 11+

INCIDENT_PENALTY = 50   # $ por cada punto de incidente
DQ_PENALTY = 200        # penalización extra por DQ (pos = 0 o muy alta)
CONTRACT_BONUS_WIN = 500  # bonus adicional si tienes contrato y ganas


def calculate_prize(finish_position: int, incidents: int,
                    has_contract: bool = False) -> float:
    """Calcula el premio neto de una carrera."""
    base = PRIZE_TABLE.get(finish_position, DEFAULT_PRIZE)
    penalty = incidents * INCIDENT_PENALTY

    # DQ: posición muy alta en iRacing
    if finish_position > 40:
        penalty += DQ_PENALTY
        base = 0

    bonus = CONTRACT_BONUS_WIN if (has_contract and finish_position == 1) else 0
    return max(base - penalty + bonus, -DQ_PENALTY)


def calculate_season_earnings(races: list[dict]) -> float:
    return sum(r.get("prize_money", 0) for r in races)


def format_money(amount: float) -> str:
    sign = "+" if amount >= 0 else ""
    return f"{sign}${amount:,.0f}"
