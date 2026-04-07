"""
Motor principal del modo carrera.
Coordina iRacing API → cálculos → BD → estado del piloto.
"""
from data import database as db
from iracing import client as ir
from core.economy import calculate_prize
from core.sanctions import evaluate_sanctions, is_pilot_banned
from core.contracts import evaluate_contract_performance


class CareerEngine:
    def __init__(self):
        self.pilot: dict | None = None
        self.stats: dict | None = None
        self.recent_races: list[dict] = []
        self.active_contract: dict | None = None
        self.active_sanctions: list[dict] = []

    async def initialize(self):
        """Inicializa la BD."""
        await db.init_db()

    async def login_and_sync(self) -> dict:
        """
        Autentica con iRacing, sincroniza datos del piloto
        y devuelve el estado completo.
        """
        # 1. Obtener info básica
        member = await ir.fetch_member_info()
        iracing_id = member["iracing_id"]

        # 2. Crear o recuperar piloto en BD
        self.pilot = await db.get_pilot(iracing_id)
        if not self.pilot:
            self.pilot = await db.create_pilot(iracing_id, member["name"])

        # 3. Stats actuales (iRating, SR)
        self.stats = await ir.fetch_driver_stats(int(iracing_id))

        # 4. Carreras recientes de iRacing
        ir_races = await ir.fetch_recent_results(int(iracing_id))

        # 5. Calcular premios y guardar carreras nuevas
        contract = await db.get_active_contract(self.pilot["id"])
        for race in ir_races:
            race["prize_money"] = calculate_prize(
                race["finish_position"],
                race["incidents"],
                has_contract=contract is not None,
            )
            saved = await db.save_race_result(self.pilot["id"], race)
            if saved:
                await db.update_balance(self.pilot["id"], race["prize_money"])

        # 6. Cargar estado completo
        self.recent_races = await db.get_recent_races(self.pilot["id"])
        self.active_contract = await db.get_active_contract(self.pilot["id"])
        self.active_sanctions = await db.get_active_sanctions(self.pilot["id"])

        # 7. Evaluar nuevas sanciones
        new_sanctions = evaluate_sanctions(self.recent_races)
        # (se guardarían en BD en una implementación completa)

        # 8. Re-leer piloto (balance actualizado)
        self.pilot = await db.get_pilot(iracing_id)

        return self.get_state()

    def get_state(self) -> dict:
        """Devuelve el estado completo para la UI."""
        banned, ban_reason = is_pilot_banned(self.active_sanctions)
        contract_status = {}
        if self.active_contract:
            contract_status = evaluate_contract_performance(
                self.active_contract, self.recent_races[:5]
            )

        return {
            "pilot": self.pilot,
            "stats": self.stats,
            "recent_races": self.recent_races,
            "active_contract": self.active_contract,
            "active_sanctions": self.active_sanctions,
            "is_banned": banned,
            "ban_reason": ban_reason,
            "contract_status": contract_status,
        }
