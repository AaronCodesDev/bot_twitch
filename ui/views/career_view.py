# ui/views/career_view.py
# Vista iRacing Career — FanTan Hub

import flet as ft
import sqlite3
import os
import sys
import asyncio
import threading
import traceback as tb
from ui.colors import *
from ui.components import *
from ui.error_logger import get_logger


BASE        = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
CAREER_DB   = os.path.join(BASE, "iracing_career", "data", "career.db")
CAREER_BASE = os.path.join(BASE, "iracing_career")
CAREER_ENV  = os.path.join(CAREER_BASE, ".env")


def _read_env() -> dict:
    """Lee el .env de iracing_career como dict."""
    env = {}
    if not os.path.exists(CAREER_ENV):
        return env
    with open(CAREER_ENV, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if line and not line.startswith("#") and "=" in line:
                k, _, v = line.partition("=")
                env[k.strip()] = v.strip()
    return env


def _write_env(env: dict) -> None:
    """Escribe el dict de vuelta al .env."""
    lines = []
    for k, v in env.items():
        lines.append(f"{k}={v}\n")
    with open(CAREER_ENV, "w", encoding="utf-8") as f:
        f.writelines(lines)


def _q(query: str, default=None):
    try:
        if not os.path.exists(CAREER_DB):
            return default
        conn = sqlite3.connect(CAREER_DB)
        conn.row_factory = sqlite3.Row
        r = conn.cursor().execute(query).fetchone()
        conn.close()
        return r[0] if r and r[0] is not None else default
    except Exception:
        return default


def _qa(query: str):
    try:
        if not os.path.exists(CAREER_DB):
            return []
        conn = sqlite3.connect(CAREER_DB)
        conn.row_factory = sqlite3.Row
        rows = conn.cursor().execute(query).fetchall()
        conn.close()
        return [dict(r) for r in rows]
    except Exception:
        return []


# ─── Estado de demo ───────────────────────────────────────────────────────────
DEMO_STATE = {
    "pilot": {"id": 1, "name": "Demo Piloto", "balance": 48200, "reputation": 62},
    "stats": {"irating": 3842, "safety_rating": 4.72, "license_class": "A", "category": "Road"},
    "recent_races": [
        {"track": "Spa-Francorchamps", "finish_position": 1, "incidents": 0,
         "irating_change": 48, "sr_change": 0.12, "prize_money": 1800, "raced_at": ""},
        {"track": "Silverstone GP", "finish_position": 2, "incidents": 1,
         "irating_change": 22, "sr_change": 0.05, "prize_money": 900, "raced_at": ""},
        {"track": "Monza", "finish_position": 5, "incidents": 2,
         "irating_change": -8, "sr_change": -0.02, "prize_money": 350, "raced_at": ""},
        {"track": "Nürburgring", "finish_position": 99, "incidents": 8,
         "irating_change": -45, "sr_change": -0.18, "prize_money": -200, "raced_at": ""},
    ],
    "active_contract": None,
    "active_sanctions": [],
    "is_banned": False,
    "ban_reason": "",
    "contract_status": {},
}

# Contratos disponibles (demo)
TEAM_OFFERS = [
    {
        "name": "Rookie Racing Team",
        "description": "Equipo de iniciación. Perfecto para empezar.",
        "salary_per_race": 800,
        "min_sr": 2.0, "min_irating": 1000, "min_wins": 0,
        "tier": 1,
    },
    {
        "name": "Amateur GT Squad",
        "description": "Escudería amateur con buenas instalaciones.",
        "salary_per_race": 1500,
        "min_sr": 3.0, "min_irating": 2000, "min_wins": 1,
        "tier": 2,
    },
    {
        "name": "Pro Circuit Racing",
        "description": "Equipo semi-profesional. Alta competición.",
        "salary_per_race": 2800,
        "min_sr": 4.0, "min_irating": 3000, "min_wins": 3,
        "tier": 3,
    },
    {
        "name": "Elite Motorsport",
        "description": "Lo más alto del iRacing competitivo.",
        "salary_per_race": 5000,
        "min_sr": 4.5, "min_irating": 4000, "min_wins": 10,
        "tier": 4,
    },
]

# Tienda — ítems relevantes para carrera en iRacing
SHOP_ITEMS = [
    # ── Staff ──────────────────────────────────────────────────────────────────
    {
        "name": "Fisioterapeuta",
        "desc": "Cuando acumulas demasiados incidentes entras en 'baja'. El fisio recorta esos días.",
        "effect": "−50 % días de baja por incidentes",
        "price": 4000, "icon": "🩺", "cat": "Staff", "accent": GREEN,
    },
    {
        "name": "Abogado de stewards",
        "desc": "Apela penalizaciones injustas. Anula puntos de incidente una vez por semana.",
        "effect": "1 apelación gratis / semana",
        "price": 6000, "icon": "⚖️", "cat": "Staff", "accent": GREEN,
    },
    {
        "name": "Psicólogo deportivo",
        "desc": "Tras rachas de malos resultados tu SR sube más lento. El psico lo acelera.",
        "effect": "+20 % velocidad de recuperación SR",
        "price": 3500, "icon": "🧠", "cat": "Staff", "accent": CYAN,
    },
    {
        "name": "Coach de academia",
        "desc": "Progresión de licencia (R→D→C→B→A) acelerada. Menos carreras requeridas por nivel.",
        "effect": "−1 carrera por ascenso de licencia",
        "price": 5000, "icon": "🎓", "cat": "Staff", "accent": CYAN,
    },
    {
        "name": "Agente personal",
        "desc": "Negocia contratos más jugosos con los equipos y añade cláusulas de bonus.",
        "effect": "+15 % salario base en contratos",
        "price": 7000, "icon": "🤝", "cat": "Staff", "accent": WARNING,
    },
    # ── Equipamiento ───────────────────────────────────────────────────────────
    {
        "name": "Simulador de entrenamiento",
        "desc": "Practica circuitos nuevos antes de competir. Menos sustos en la primera carrera.",
        "effect": "−30 % incidentes en pistas desconocidas",
        "price": 8000, "icon": "🖥️", "cat": "Equipamiento", "accent": ORANGE,
    },
    {
        "name": "Pack de telemetría avanzada",
        "desc": "Análisis de cada vuelta. Identifica dónde pierdes tiempo y mejora tu consistencia.",
        "effect": "+10 % ganancia de iRating por carrera",
        "price": 5500, "icon": "📡", "cat": "Equipamiento", "accent": ORANGE,
    },
    {
        "name": "Ingeniero de setup",
        "desc": "Setups personalizados por circuito. Salidas más adelantadas en la parrilla.",
        "effect": "+2 posiciones en clasificación media",
        "price": 4500, "icon": "🔧", "cat": "Equipamiento", "accent": ORANGE,
    },
    # ── Estrategia ─────────────────────────────────────────────────────────────
    {
        "name": "Ingeniero de estrategia",
        "desc": "Pit stops en el momento justo, gestión de neumáticos. Clave en endurance.",
        "effect": "+25 % ingresos en carreras de resistencia",
        "price": 6500, "icon": "📋", "cat": "Estrategia", "accent": PURPLE,
    },
    {
        "name": "Asesor de series",
        "desc": "Te abre puertas antes de tiempo. Accede a una serie por encima de tu licencia.",
        "effect": "Desbloquea 1 serie de nivel superior",
        "price": 12000, "icon": "🔓", "cat": "Estrategia", "accent": PURPLE,
    },
    # ── Financiero ─────────────────────────────────────────────────────────────
    {
        "name": "Patrocinador personal",
        "desc": "Ingresos fijos por carrera sin importar el resultado. Como llevar un sponsor en el casco.",
        "effect": "+$300 por carrera completada",
        "price": 10000, "icon": "🏷️", "cat": "Financiero", "accent": GREEN,
    },
]

# Retos disponibles
CHALLENGES = [
    # Qualifying
    {
        "id": "quali_top10",
        "title": "La qualy perfecta",
        "desc": "Termina una clasificación en el top 10 % de tu split",
        "type": "Qualifying", "icon": "⏱️",
        "reward_money": 500, "reward_rep": 3,
        "condition": "finish_position <= 3",
    },
    {
        "id": "quali_pole",
        "title": "Pole position",
        "desc": "Consigue la pole en cualquier serie",
        "type": "Qualifying", "icon": "🟡",
        "reward_money": 1000, "reward_rep": 8,
        "condition": "finish_position == 1",
    },
    # Carrera limpia
    {
        "id": "clean_race",
        "title": "Carrera limpia",
        "desc": "Termina una carrera con 0 incidentes",
        "type": "Limpieza", "icon": "✨",
        "reward_money": 400, "reward_rep": 5,
        "condition": "incidents == 0",
    },
    {
        "id": "clean_streak",
        "title": "Piloto de guante blanco",
        "desc": "3 carreras consecutivas con 0 incidentes",
        "type": "Limpieza", "icon": "🧤",
        "reward_money": 1500, "reward_rep": 15,
        "condition": "streak_clean >= 3",
    },
    # Remontadas
    {
        "id": "comeback",
        "title": "Remontada épica",
        "desc": "Salir desde P12 o más atrás y acabar en el top 5",
        "type": "Remontada", "icon": "🚀",
        "reward_money": 800, "reward_rep": 10,
        "condition": "start_pos >= 12 and finish_position <= 5",
    },
    {
        "id": "last_to_first",
        "title": "De último a primero",
        "desc": "Ganar saliendo desde el último puesto de la parrilla",
        "type": "Remontada", "icon": "🦅",
        "reward_money": 3000, "reward_rep": 25,
        "condition": "start_pos == last and finish_position == 1",
    },
    # Rachas
    {
        "id": "hat_trick",
        "title": "Hat trick",
        "desc": "3 podios consecutivos en cualquier serie",
        "type": "Racha", "icon": "🎩",
        "reward_money": 2000, "reward_rep": 20,
        "condition": "streak_podium >= 3",
    },
    {
        "id": "win_streak",
        "title": "Dominador",
        "desc": "2 victorias seguidas",
        "type": "Racha", "icon": "👑",
        "reward_money": 2500, "reward_rep": 18,
        "condition": "streak_wins >= 2",
    },
    {
        "id": "consistent",
        "title": "Máquina de puntuar",
        "desc": "10 finales consecutivos sin abandonar",
        "type": "Racha", "icon": "🏁",
        "reward_money": 1200, "reward_rep": 12,
        "condition": "streak_finishes >= 10",
    },
    # Licencia
    {
        "id": "sr_perfect",
        "title": "Licencia de diamante",
        "desc": "Mantén SR > 4.5 durante 5 carreras seguidas",
        "type": "Licencia", "icon": "💎",
        "reward_money": 0, "reward_rep": 30,
        "condition": "sr_streak_45 >= 5",
    },
    {
        "id": "upgrade_license",
        "title": "Ascenso de licencia",
        "desc": "Consigue ascender de clase (ej. C → B)",
        "type": "Licencia", "icon": "🆙",
        "reward_money": 3000, "reward_rep": 20,
        "condition": "license_upgraded == True",
    },
]


class CareerView:
    def __init__(self, state: dict, page: ft.Page):
        self.state = state
        self.page = page
        self._career_data = None
        self._is_demo = True
        self._tab_ref = ft.Ref[ft.Tabs]()

    def _load_data(self) -> dict:
        # Intentar cargar desde BD real
        try:
            pilot = _qa("SELECT * FROM pilots LIMIT 1")
            if pilot:
                p = pilot[0]
                races = _qa("""
                    SELECT track, finish_position, incidents, irating_change,
                           sr_change, prize_money, raced_at
                    FROM results WHERE pilot_id=1
                    ORDER BY raced_at DESC LIMIT 10
                """)
                self._is_demo = False
                return {
                    "pilot": p,
                    "stats": {"irating": 0, "safety_rating": 0,
                              "license_class": "?", "category": "Road"},
                    "recent_races": races,
                    "active_contract": None,
                    "active_sanctions": [],
                    "is_banned": False,
                    "ban_reason": "",
                    "contract_status": {},
                }
        except Exception:
            pass
        self._is_demo = True
        return DEMO_STATE

    # ─── Build principal ──────────────────────────────────────────────────────
    def build(self) -> ft.Control:
        self._career_data = self._load_data()
        data = self._career_data

        sync_ref = ft.Ref[ft.Text]()

        # Detectar si hay credenciales configuradas
        env_data  = _read_env()
        has_creds = bool(env_data.get("IRACING_USERNAME", "").strip()
                         and env_data.get("IRACING_PASSWORD", "").strip())

        token_btn = ft.ElevatedButton(
            content=ft.Row([
                ft.Icon(ft.Icons.PERSON_ROUNDED, size=15,
                        color="white" if has_creds else WARNING),
                ft.Text("Credenciales" if has_creds else "Configurar cuenta",
                        size=12,
                        color="white" if has_creds else WARNING,
                        weight=ft.FontWeight.W_600),
            ], spacing=6, tight=True),
            bgcolor=with_alpha(GREEN, 0.4) if has_creds else SURFACE3,
            style=ft.ButtonStyle(shape=ft.RoundedRectangleBorder(radius=10), elevation=0),
            on_click=lambda e: self._show_token_dialog(),
            tooltip="Email y contraseña de iRacing",
        )

        sync_btn = ft.ElevatedButton(
            content=ft.Row([
                ft.Icon(ft.Icons.SYNC_ROUNDED, size=15, color="white"),
                ft.Text("Sincronizar", size=12, color="white", weight=ft.FontWeight.W_600),
            ], spacing=6, tight=True),
            bgcolor=GREEN,
            style=ft.ButtonStyle(shape=ft.RoundedRectangleBorder(radius=10), elevation=0),
            on_click=lambda e: self._do_sync(sync_ref),
        )

        header = module_header(
            "🏆", "iRacing Career",
            subtitle="Modo carrera — gestión de tu carrera virtual",
            accent=GREEN,
            actions=[
                ft.Container(
                    content=ft.Text(
                        ref=sync_ref,
                        value="Modo demo" if self._is_demo else "Sincronizado",
                        size=11,
                        color=WARNING if self._is_demo else GREEN,
                    ),
                    border=ft.border.all(1, with_alpha(GREEN, 0.3)),
                    border_radius=8,
                    padding=ft.padding.symmetric(horizontal=10, vertical=5),
                ),
                token_btn,
                sync_btn,
            ],
        )

        pilot = data.get("pilot", {})
        stats = data.get("stats", {})
        races = data.get("recent_races", [])
        is_banned = data.get("is_banned", False)

        wins = sum(1 for r in races if r.get("finish_position") == 1)
        season_earn = sum(r.get("prize_money", 0) or 0 for r in races)
        balance = pilot.get("balance", 0) or 0
        irating = stats.get("irating", 0) or 0
        sr = stats.get("safety_rating", 0) or 0

        # Ban alert
        ban_alert = ft.Container(
            content=ft.Row([
                ft.Icon(ft.Icons.DO_NOT_DISTURB_ROUNDED, color=DANGER, size=16),
                ft.Text(f"Piloto suspendido — {data.get('ban_reason', '')}",
                        color=DANGER, size=12),
            ], spacing=8),
            bgcolor=with_alpha(DANGER, 0.06),
            border=ft.border.all(0.5, with_alpha(DANGER, 0.3)),
            border_radius=10,
            padding=12,
            visible=is_banned,
        )

        tabs = ft.Tabs(
            ref=self._tab_ref,
            selected_index=0,
            animation_duration=250,
            tab_alignment=ft.TabAlignment.START,
            indicator_color=GREEN,
            label_color=GREEN,
            unselected_label_color=MUTED,
            tabs=[
                ft.Tab(text="Dashboard", icon=ft.Icons.DASHBOARD_OUTLINED,
                       content=self._build_dashboard_tab(data)),
                ft.Tab(text="Perfil", icon=ft.Icons.PERSON_ROUNDED,
                       content=self._build_profile_tab(data)),
                ft.Tab(text="Contratos", icon=ft.Icons.DESCRIPTION_OUTLINED,
                       content=self._build_contracts_tab(stats, races)),
                ft.Tab(text="Tienda", icon=ft.Icons.STOREFRONT_OUTLINED,
                       content=self._build_shop_tab(balance)),
                ft.Tab(text="Retos", icon=ft.Icons.FLAG_OUTLINED,
                       content=self._build_challenges_tab()),
                ft.Tab(text="Sanciones", icon=ft.Icons.WARNING_AMBER_OUTLINED,
                       content=self._build_sanctions_tab(data)),
            ],
            expand=True,
        )

        return ft.Column([
            header,
            ft.Container(height=10),
            ban_alert if is_banned else ft.Container(height=0),
            ft.Container(content=tabs, expand=True),
        ], spacing=0, expand=True)

    # ─── Dashboard tab ────────────────────────────────────────────────────────
    def _build_dashboard_tab(self, data: dict) -> ft.Container:
        races = data.get("recent_races", [])
        stats = data.get("stats", {})
        contract = data.get("active_contract")
        pilot = data.get("pilot", {})

        # Stats compactas superiores
        _wins    = sum(1 for r in races if r.get("finish_position") == 1)
        _earn    = sum(r.get("prize_money", 0) or 0 for r in races)
        _balance = pilot.get("balance", 0) or 0
        _irating = stats.get("irating", 0) or 0
        _sr      = stats.get("safety_rating", 0) or 0

        def _cs(icon, label, value, accent):
            return ft.Container(
                content=ft.Row([
                    ft.Text(icon, size=14),
                    ft.Column([
                        ft.Text(value, size=14, weight=ft.FontWeight.W_800, color=TEXT),
                        ft.Text(label, size=9, color=MUTED),
                    ], spacing=0, expand=True),
                ], spacing=7),
                bgcolor=with_alpha(accent, 0.06),
                border_radius=9,
                border=ft.border.only(left=ft.BorderSide(2, accent)),
                padding=ft.padding.symmetric(horizontal=11, vertical=7),
                expand=True,
            )

        dash_stats = ft.Row([
            _cs("📈", "iRating",   str(_irating) if _irating else "---", GREEN),
            _cs("🛡️", "Safety R.", f"{_sr:.2f}" if _sr else "---",       GREEN),
            _cs("🥇", "Victorias", str(_wins),                            WARNING),
            _cs("💰", "Balance",   f"${_balance:,.0f}",                   GREEN),
        ], spacing=8, expand=True)

        # Últimas carreras
        race_rows = []
        for r in races[:8]:
            pos = r.get("finish_position", 0) or 0
            inc = r.get("incidents", 0) or 0
            money = r.get("prize_money", 0) or 0
            ir_change = r.get("irating_change", 0) or 0
            sr_change = r.get("sr_change", 0) or 0

            is_dq = pos > 40
            pos_color = (WARNING if pos == 1 else
                         GREEN if pos <= 3 else
                         DANGER if is_dq else MUTED)
            pos_label = "DQ" if is_dq else str(pos)

            race_rows.append(
                ft.Container(
                    content=ft.Row([
                        ft.Container(
                            content=ft.Text(pos_label, size=11, color=pos_color,
                                            weight=ft.FontWeight.W_700,
                                            text_align=ft.TextAlign.CENTER),
                            width=32, height=28,
                            bgcolor=with_alpha(pos_color, 0.12),
                            border=ft.border.all(0.5, with_alpha(pos_color, 0.4)),
                            border_radius=6,
                            alignment=ft.Alignment(0, 0),
                        ),
                        ft.Column([
                            ft.Text(r.get("track", "?"), size=12, color=TEXT,
                                    weight=ft.FontWeight.W_500),
                            ft.Text(f"{inc}x inc.", size=10, color=MUTED),
                        ], spacing=1, expand=True),
                        ft.Column([
                            ft.Text(f"{'+'if ir_change >= 0 else ''}{ir_change} iR",
                                    size=11, color=GREEN if ir_change >= 0 else DANGER,
                                    weight=ft.FontWeight.W_600),
                            ft.Text(f"{'+'if sr_change >= 0 else ''}{sr_change:.2f} SR",
                                    size=10, color=GREEN if sr_change >= 0 else DANGER),
                        ], spacing=2),
                        ft.Text(f"${money:,.0f}" if money >= 0 else f"-${abs(money):,.0f}",
                                size=12, color=GREEN if money >= 0 else DANGER,
                                weight=ft.FontWeight.W_600, width=80,
                                text_align=ft.TextAlign.RIGHT),
                    ], spacing=10),
                    border=ft.border.only(bottom=ft.BorderSide(0.5, BORDER)),
                    padding=ft.padding.symmetric(vertical=9),
                )
            )

        races_panel = ft.Container(
            content=ft.Column([
                ft.Text("ÚLTIMAS CARRERAS", size=10, color=MUTED, weight=ft.FontWeight.W_500),
                ft.Container(height=10),
                ft.Column(race_rows if race_rows else [
                    ft.Text("Sin carreras registradas", size=12, color=MUTED)
                ], spacing=0),
            ], spacing=0),
            bgcolor=SURFACE,
            border_radius=14,
            border=ft.border.all(1, BORDER2),
            padding=16,
            expand=True,
        )

        # Quick info panel
        lic = stats.get("license_class", "?")
        cat = stats.get("category", "Road")
        team = contract["team_name"] if contract else "Freelance"
        rep = pilot.get("reputation", 62) or 62

        # Reputation bar
        rep_bar = ft.Column([
            ft.Row([
                ft.Text("Reputación", size=11, color=MUTED, expand=True),
                ft.Text(f"{rep}/100", size=11, color=GREEN, weight=ft.FontWeight.W_600),
            ]),
            ft.ProgressBar(
                value=rep / 100,
                color=GREEN if rep >= 60 else (WARNING if rep >= 30 else DANGER),
                bgcolor=SURFACE3, height=5, border_radius=3,
            ),
        ], spacing=5)

        quick_panel = ft.Container(
            content=ft.Column([
                ft.Text("ESTADO ACTUAL", size=10, color=MUTED, weight=ft.FontWeight.W_500),
                ft.Container(height=10),
                ft.Divider(height=1, color=BORDER),
                ft.Container(height=8),
                info_row("Licencia", f"Clase {lic} · {cat}"),
                info_row("Equipo", team, GREEN if team != "Freelance" else MUTED),
                info_row("Categoría", cat),
                ft.Container(height=8),
                rep_bar,
                ft.Container(height=14),
                primary_button(
                    "Ver contratos →", None, GREEN,
                    on_click=lambda e: setattr(self._tab_ref.current, 'selected_index', 1) or self.page.update(),
                    expand=True,
                ),
            ], spacing=8),
            bgcolor=SURFACE,
            border_radius=14,
            border=ft.border.all(1, BORDER2),
            padding=16,
            width=220,
        )

        return ft.Container(
            content=ft.Column([
                ft.Container(height=12),
                dash_stats,
                ft.Container(height=10),
                ft.Row([races_panel, quick_panel], spacing=14, expand=True),
            ], spacing=0, scroll=ft.ScrollMode.AUTO, expand=True),
            expand=True,
        )

    # ─── Contracts tab ────────────────────────────────────────────────────────
    def _build_contracts_tab(self, stats: dict, races: list) -> ft.Container:
        irating = stats.get("irating", 0) or 0
        sr = stats.get("safety_rating", 0.0) or 0.0
        wins = sum(1 for r in races if r.get("finish_position") == 1)

        tier_colors = {1: MUTED, 2: INFO, 3: GREEN, 4: PURPLE}

        cards = []
        for t in TEAM_OFFERS:
            can_sign = (sr >= t["min_sr"] and
                        irating >= t["min_irating"] and
                        wins >= t["min_wins"])
            accent = tier_colors.get(t["tier"], MUTED)

            req_pills = ft.Row([
                self._req_pill(f"SR ≥ {t['min_sr']}", sr >= t["min_sr"]),
                self._req_pill(f"iR ≥ {t['min_irating']}", irating >= t["min_irating"]),
                self._req_pill(f"{t['min_wins']} vic.", wins >= t["min_wins"]),
            ], spacing=6, wrap=True)

            card_ctrl = ft.Container(
                content=ft.Column([
                    ft.Row([
                        ft.Container(
                            content=ft.Text("🏎️", size=20),
                            width=40, height=40,
                            bgcolor=with_alpha(accent, 0.12),
                            border_radius=10,
                            alignment=ft.Alignment(0, 0),
                        ),
                        ft.Column([
                            ft.Text(t["name"], size=14, weight=ft.FontWeight.W_700, color=TEXT),
                            ft.Text(t["description"], size=11, color=MUTED),
                        ], spacing=2, expand=True),
                        ft.Column([
                            ft.Text(f"${t['salary_per_race']:,}", size=16,
                                    color=GREEN, weight=ft.FontWeight.W_700),
                            ft.Text("por carrera", size=10, color=MUTED),
                        ], spacing=2, horizontal_alignment=ft.CrossAxisAlignment.END),
                    ], spacing=10),
                    ft.Container(height=10),
                    req_pills,
                    ft.Container(height=10),
                    primary_button(
                        "✅ Firmar contrato" if can_sign else "🔒 Requisitos no cumplidos",
                        None,
                        GREEN if can_sign else MUTED2,
                        on_click=(lambda e, tn=t["name"]: self._sign_contract(tn)) if can_sign else None,
                        expand=True,
                    ) if can_sign else secondary_button(
                        "🔒 Requisitos no cumplidos",
                        None, MUTED2, expand=True,
                    ),
                ], spacing=0),
                bgcolor=SURFACE,
                border_radius=14,
                border=ft.border.all(1, with_alpha(accent, 0.3) if can_sign else BORDER),
                padding=16,
            )
            cards.append(card_ctrl)

        return ft.Container(
            content=ft.Column([
                ft.Container(height=12),
                section_title("Ofertas de equipos disponibles", accent=GREEN),
                ft.Container(height=10),
                ft.Column(cards, spacing=12),
            ], spacing=0, scroll=ft.ScrollMode.AUTO, expand=True),
            expand=True,
        )

    def _req_pill(self, label: str, ok: bool) -> ft.Container:
        return ft.Container(
            content=ft.Row([
                ft.Text("✓" if ok else "✗", size=10,
                        color=GREEN if ok else DANGER, weight=ft.FontWeight.W_700),
                ft.Text(label, size=10, color=GREEN if ok else DANGER),
            ], spacing=4),
            bgcolor=with_alpha(GREEN if ok else DANGER, 0.08),
            border=ft.border.all(0.5, with_alpha(GREEN if ok else DANGER, 0.3)),
            border_radius=12,
            padding=ft.padding.symmetric(horizontal=8, vertical=3),
        )

    def _sign_contract(self, team_name: str):
        dlg = ft.AlertDialog(
            title=ft.Text("Firmar contrato", weight=ft.FontWeight.W_700),
            content=ft.Column([
                ft.Text(f"¿Firmar con {team_name}?", size=13, color=TEXT),
                ft.Text("Esta acción registrará el contrato en tu carrera.",
                        size=11, color=MUTED),
            ], spacing=8, tight=True),
            actions=[
                ft.TextButton("Cancelar", on_click=lambda e: self.page.close(dlg)),
                ft.ElevatedButton(
                    "Firmar",
                    bgcolor=GREEN,
                    style=ft.ButtonStyle(color="white"),
                    on_click=lambda e: (
                        self.page.close(dlg),
                        self._show_toast(f"✅ Contrato firmado con {team_name}"),
                    ),
                ),
            ],
        )
        self.page.open(dlg)

    # ─── Shop tab ─────────────────────────────────────────────────────────────
    def _build_shop_tab(self, balance: int) -> ft.Container:
        owned_names = {r["item_name"] for r in _qa(
            "SELECT item_name FROM owned_item WHERE pilot_id=1")}

        # Agrupar por categoría
        cats: dict[str, list] = {}
        for item in SHOP_ITEMS:
            cats.setdefault(item["cat"], []).append(item)

        cat_icons = {
            "Staff": "👥", "Equipamiento": "🛠️",
            "Estrategia": "📐", "Financiero": "💼",
        }

        sections = []
        for cat_name, cat_items in cats.items():
            cards = []
            for item in cat_items:
                accent    = item.get("accent", GREEN)
                owned     = item["name"] in owned_names
                can_buy   = (not owned) and balance >= item["price"]
                is_locked = (not owned) and balance < item["price"]

                state_label = "Ya tienes esto" if owned else (
                    "Comprar" if can_buy else f"Faltan ${item['price'] - balance:,}")
                state_color = MUTED2 if owned else (GREEN if can_buy else DANGER)

                cards.append(ft.Container(
                    content=ft.Row([
                        # Icono
                        ft.Container(
                            content=ft.Text(item["icon"], size=22),
                            width=46, height=46,
                            bgcolor=with_alpha(accent, 0.10 if not owned else 0.05),
                            border_radius=11,
                            alignment=ft.Alignment(0, 0),
                            border=ft.border.all(1, with_alpha(accent, 0.2)),
                        ),
                        # Info
                        ft.Column([
                            ft.Row([
                                ft.Text(item["name"], size=12,
                                        weight=ft.FontWeight.W_700, color=TEXT if not owned else MUTED),
                                ft.Container(
                                    content=ft.Text(item["cat"], size=8,
                                                    color=accent, weight=ft.FontWeight.W_600),
                                    bgcolor=with_alpha(accent, 0.10),
                                    border_radius=6,
                                    padding=ft.padding.symmetric(horizontal=6, vertical=2),
                                ),
                            ], spacing=7),
                            ft.Text(item["desc"], size=10, color=MUTED),
                            ft.Container(
                                content=ft.Row([
                                    ft.Text("⚡", size=10),
                                    ft.Text(item["effect"], size=10,
                                            color=accent, weight=ft.FontWeight.W_600),
                                ], spacing=4),
                                bgcolor=with_alpha(accent, 0.06),
                                border_radius=5,
                                padding=ft.padding.symmetric(horizontal=7, vertical=3),
                            ),
                        ], spacing=4, expand=True),
                        # Precio + botón
                        ft.Column([
                            ft.Text(f"${item['price']:,}", size=13,
                                    color=GREEN if not owned else MUTED2,
                                    weight=ft.FontWeight.W_800),
                            ft.Container(
                                content=ft.Text(
                                    state_label, size=10,
                                    color="white" if can_buy else state_color,
                                    weight=ft.FontWeight.W_600,
                                ),
                                bgcolor=with_alpha(state_color, 0.85) if can_buy else with_alpha(state_color, 0.08),
                                border=ft.border.all(1, with_alpha(state_color, 0.3)) if not can_buy else None,
                                border_radius=7,
                                padding=ft.padding.symmetric(horizontal=10, vertical=5),
                                on_click=(lambda e, n=item["name"], p=item["price"]:
                                          self._buy_item(n, p)) if can_buy else None,
                            ),
                        ], spacing=5, horizontal_alignment=ft.CrossAxisAlignment.END),
                    ], spacing=10),
                    bgcolor=with_alpha(accent, 0.03) if not owned else SURFACE2,
                    border_radius=12,
                    border=ft.border.all(1, with_alpha(accent, 0.18) if can_buy else BORDER),
                    padding=ft.padding.symmetric(horizontal=14, vertical=11),
                ))

            sections.append(ft.Container(height=6))
            sections.append(ft.Row([
                ft.Text(f"{cat_icons.get(cat_name,'📦')} {cat_name.upper()}",
                        size=9, color=MUTED, weight=ft.FontWeight.W_700),
                ft.Container(expand=True, height=1, bgcolor=BORDER2),
            ], spacing=10, vertical_alignment=ft.CrossAxisAlignment.CENTER))
            sections.append(ft.Container(height=6))
            sections.append(ft.Column(cards, spacing=7))

        balance_bar = ft.Container(
            content=ft.Row([
                ft.Text("💰", size=18),
                ft.Column([
                    ft.Text("Balance disponible", size=10, color=MUTED),
                    ft.Text(f"${balance:,.0f}", size=18, color=GREEN,
                            weight=ft.FontWeight.W_800),
                ], spacing=1),
                ft.Container(expand=True),
                ft.Text(f"{len(owned_names)} ítems activos", size=10, color=MUTED),
            ], spacing=12),
            bgcolor=with_alpha(GREEN, 0.06),
            border=ft.border.all(1, with_alpha(GREEN, 0.2)),
            border_radius=10,
            padding=ft.padding.symmetric(horizontal=14, vertical=10),
        )

        return ft.Container(
            content=ft.Column(
                [ft.Container(height=12), balance_bar] + sections,
                spacing=0, scroll=ft.ScrollMode.AUTO, expand=True,
            ),
            expand=True,
        )

    def _buy_item(self, name: str, price: int):
        self._show_toast(f"✅ Compraste: {name} (${price:,})")

    # ─── Challenges tab ───────────────────────────────────────────────────────
    def _build_challenges_tab(self) -> ft.Container:
        completed = {r["challenge_id"] for r in _qa(
            "SELECT challenge_id FROM completed_challenges WHERE pilot_id=1"
        )} if os.path.exists(CAREER_DB) else set()

        type_colors = {
            "Qualifying": CYAN, "Limpieza": GREEN, "Remontada": ORANGE,
            "Racha": PURPLE, "Licencia": WARNING,
        }
        type_icons = {
            "Qualifying": "⏱️", "Limpieza": "✨", "Remontada": "🚀",
            "Racha": "🔥", "Licencia": "🪪",
        }

        # Agrupar por tipo
        by_type: dict[str, list] = {}
        for ch in CHALLENGES:
            by_type.setdefault(ch["type"], []).append(ch)

        sections = []
        total_done = 0

        for type_name, challenges in by_type.items():
            accent = type_colors.get(type_name, MUTED2)
            t_icon = type_icons.get(type_name, "🏁")
            cards  = []

            for ch in challenges:
                done = ch["id"] in completed
                if done:
                    total_done += 1

                reward_parts = []
                if ch["reward_money"]:
                    reward_parts.append(f"${ch['reward_money']:,}")
                if ch["reward_rep"]:
                    reward_parts.append(f"+{ch['reward_rep']} rep")
                reward_str = "  ·  ".join(reward_parts) or "—"

                cards.append(ft.Container(
                    content=ft.Row([
                        # Icono + check
                        ft.Stack([
                            ft.Container(
                                content=ft.Text(ch["icon"], size=20),
                                width=42, height=42,
                                bgcolor=with_alpha(accent, 0.08 if not done else 0.15),
                                border_radius=10,
                                alignment=ft.Alignment(0, 0),
                            ),
                            ft.Container(
                                content=ft.Text("✓", size=11, color="white",
                                                weight=ft.FontWeight.W_900),
                                width=16, height=16,
                                bgcolor=GREEN,
                                border_radius=8,
                                alignment=ft.Alignment(0, 0),
                                right=0, bottom=0,
                                visible=done,
                            ),
                        ], width=42, height=42),
                        # Texto
                        ft.Column([
                            ft.Text(ch["title"], size=12, weight=ft.FontWeight.W_700,
                                    color=MUTED if done else TEXT),
                            ft.Text(ch["desc"], size=10, color=MUTED),
                        ], spacing=2, expand=True),
                        # Recompensa
                        ft.Container(
                            content=ft.Column([
                                ft.Text("PREMIO", size=8, color=MUTED,
                                        weight=ft.FontWeight.W_600),
                                ft.Text(reward_str, size=11,
                                        color=GREEN if not done else MUTED2,
                                        weight=ft.FontWeight.W_700),
                            ], spacing=2, horizontal_alignment=ft.CrossAxisAlignment.END),
                        ),
                    ], spacing=10),
                    bgcolor=with_alpha(GREEN, 0.03) if done else SURFACE,
                    border_radius=11,
                    border=ft.border.all(
                        1, with_alpha(GREEN, 0.3) if done else with_alpha(accent, 0.15)
                    ),
                    padding=ft.padding.symmetric(horizontal=13, vertical=10),
                ))

            sections.append(ft.Container(height=8))
            sections.append(ft.Row([
                ft.Container(
                    content=ft.Text(f"{t_icon} {type_name.upper()}",
                                    size=9, color=accent, weight=ft.FontWeight.W_700),
                    bgcolor=with_alpha(accent, 0.08),
                    border_radius=6,
                    padding=ft.padding.symmetric(horizontal=8, vertical=3),
                ),
                ft.Container(expand=True, height=1, bgcolor=BORDER2),
                ft.Text(f"{sum(1 for c in challenges if c['id'] in completed)}/{len(challenges)}",
                        size=9, color=MUTED),
            ], spacing=10, vertical_alignment=ft.CrossAxisAlignment.CENTER))
            sections.append(ft.Container(height=6))
            sections.append(ft.Column(cards, spacing=6))

        total = len(CHALLENGES)
        pct   = total_done / total if total else 0

        header_card = ft.Container(
            content=ft.Column([
                ft.Row([
                    ft.Column([
                        ft.Text("🏆 Retos de carrera", size=13,
                                weight=ft.FontWeight.W_800, color=TEXT),
                        ft.Text("Completa desafíos para ganar dinero y reputación",
                                size=10, color=MUTED),
                    ], spacing=2, expand=True),
                    ft.Column([
                        ft.Text(f"{total_done}/{total}", size=18,
                                weight=ft.FontWeight.W_900, color=WARNING),
                        ft.Text("completados", size=9, color=MUTED),
                    ], spacing=1, horizontal_alignment=ft.CrossAxisAlignment.END),
                ]),
                ft.Container(height=8),
                ft.ProgressBar(value=pct, color=WARNING, bgcolor=SURFACE3,
                               height=5, border_radius=3),
            ], spacing=0),
            bgcolor=with_alpha(WARNING, 0.05),
            border=ft.border.all(1, with_alpha(WARNING, 0.2)),
            border_radius=12,
            padding=ft.padding.symmetric(horizontal=14, vertical=12),
        )

        return ft.Container(
            content=ft.Column(
                [ft.Container(height=12), header_card] + sections,
                spacing=0, scroll=ft.ScrollMode.AUTO, expand=True,
            ),
            expand=True,
        )

    # ─── Sanctions tab ────────────────────────────────────────────────────────
    def _build_sanctions_tab(self, data: dict) -> ft.Container:
        sanctions = data.get("active_sanctions", [])
        is_banned = data.get("is_banned", False)

        sanctions_widgets = []
        if not sanctions and not is_banned:
            sanctions_widgets = [
                ft.Container(
                    content=ft.Column([
                        ft.Text("✅", size=48, text_align=ft.TextAlign.CENTER),
                        ft.Text("Sin sanciones activas", size=16, color=GREEN,
                                weight=ft.FontWeight.W_600, text_align=ft.TextAlign.CENTER),
                        ft.Text("¡Estás limpio! Sigue así.", size=12, color=MUTED,
                                text_align=ft.TextAlign.CENTER),
                    ], horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                       alignment=ft.MainAxisAlignment.CENTER, spacing=10),
                    alignment=ft.Alignment(0, 0),
                    expand=True,
                )
            ]
        else:
            for s in sanctions:
                sanctions_widgets.append(
                    ft.Container(
                        content=ft.Row([
                            ft.Icon(ft.Icons.WARNING_AMBER_ROUNDED, color=WARNING, size=20),
                            ft.Column([
                                ft.Text(s.get("reason", "Sanción"), size=13,
                                        color=TEXT, weight=ft.FontWeight.W_500),
                                ft.Text(f"Hasta: {s.get('ends_at', '?')}",
                                        size=11, color=MUTED),
                            ], spacing=2, expand=True),
                        ], spacing=10),
                        bgcolor=with_alpha(WARNING, 0.06),
                        border=ft.border.all(1, with_alpha(WARNING, 0.3)),
                        border_radius=10,
                        padding=14,
                    )
                )

        # Historial de incidentes desde tracker
        inc_history = []
        try:
            from ui.colors import TRACKER_DB  # type: ignore
        except Exception:
            pass
        tracker_db = os.path.join(BASE, "..", "Iracing_tracker", "iracing_data.db")
        try:
            if os.path.exists(tracker_db):
                conn = sqlite3.connect(tracker_db)
                conn.row_factory = sqlite3.Row
                rows = conn.cursor().execute("""
                    SELECT track_name, total_incidents, session_date
                    FROM sessions WHERE total_incidents > 0
                    ORDER BY session_date DESC LIMIT 5
                """).fetchall()
                conn.close()
                inc_history = [dict(r) for r in rows]
        except Exception:
            pass

        inc_rows = []
        for r in inc_history:
            inc = r.get("total_incidents", 0)
            inc_rows.append([
                r.get("track_name", "?"),
                ft.Container(
                    content=ft.Text(f"{inc}x", size=12,
                                    color=DANGER if inc >= 4 else (WARNING if inc >= 2 else MUTED),
                                    weight=ft.FontWeight.W_700),
                    expand=True,
                ),
                r.get("session_date", "---")[:10] if r.get("session_date") else "---",
            ])

        return ft.Container(
            content=ft.Column([
                ft.Container(height=12),
                section_title("Sanciones activas", accent=DANGER),
                ft.Container(height=10),
                ft.Column(sanctions_widgets, expand=True if not sanctions else False, spacing=8),
                ft.Container(height=16),
                section_title("Incidentes recientes (Tracker)", accent=WARNING),
                ft.Container(height=8),
                simple_table(
                    ["Circuito", "Incidentes", "Fecha"],
                    inc_rows if inc_rows else [["Sin datos del tracker", "---", "---"]],
                    accent=WARNING,
                ) if inc_history else ft.Container(
                    content=ft.Text("Conecta el iRacing Tracker para ver incidentes",
                                    size=12, color=MUTED),
                    padding=10,
                ),
            ], spacing=0, scroll=ft.ScrollMode.AUTO, expand=True),
            expand=True,
        )

    # ─── Diálogo de credenciales ──────────────────────────────────────────────
    def _show_token_dialog(self):
        env_data = _read_env()

        user_field = ft.TextField(
            value=env_data.get("IRACING_USERNAME", ""),
            label="Email de iRacing",
            hint_text="tu@email.com",
            border_color=GREEN, focused_border_color=GREEN,
            text_size=12, expand=True,
        )
        pass_field = ft.TextField(
            value=env_data.get("IRACING_PASSWORD", ""),
            label="Contraseña de iRacing (sin 2FA)",
            hint_text="Solo si NO tienes 2FA activado",
            password=True, can_reveal_password=True,
            border_color=GREEN, focused_border_color=GREEN,
            text_size=12, expand=True,
        )
        cookie_field = ft.TextField(
            value=env_data.get("IRACING_COOKIE", ""),
            label="Cookie  irsso_membersv3  (con 2FA)",
            hint_text="Pégala si tienes 2FA activado",
            password=True, can_reveal_password=True,
            border_color=ORANGE, focused_border_color=ORANGE,
            text_size=12, expand=True,
        )

        def save_creds(e):
            env_data["IRACING_USERNAME"] = user_field.value.strip()
            env_data["IRACING_PASSWORD"] = pass_field.value.strip()
            env_data["IRACING_COOKIE"]   = cookie_field.value.strip()
            env_data.pop("IRACING_ACCESS_TOKEN", None)
            _write_env(env_data)
            for k in ("IRACING_USERNAME", "IRACING_PASSWORD", "IRACING_COOKIE"):
                os.environ[k] = env_data.get(k, "")
            self.page.close(dlg)
            self._show_toast("✅ Credenciales guardadas — pulsa Sincronizar", color=GREEN)

        info_normal = ft.Container(
            content=ft.Row([
                ft.Icon(ft.Icons.INFO_OUTLINE_ROUNDED, color=CYAN, size=14),
                ft.Text("Sin 2FA: rellena email + contraseña y listo.",
                        size=11, color=MUTED, expand=True),
            ], spacing=8),
            bgcolor=with_alpha(CYAN, 0.05),
            border=ft.border.all(1, with_alpha(CYAN, 0.15)),
            border_radius=8, padding=10,
        )

        info_2fa = ft.Container(
            content=ft.Column([
                ft.Row([
                    ft.Icon(ft.Icons.LOCK_OUTLINED, color=ORANGE, size=14),
                    ft.Text("Con 2FA activo — cómo obtener la cookie:",
                            size=11, color=ORANGE, weight=ft.FontWeight.W_600),
                ], spacing=6),
                ft.Text(
                    "1.  Entra en  members-ng.iracing.com  con tu 2FA en el navegador\n"
                    "2.  Pulsa  F12  →  Application  →  Cookies  →  members-ng.iracing.com\n"
                    "3.  Busca la cookie:  irsso_membersv3\n"
                    "4.  Copia su  Value  y pégalo en el campo naranja de abajo",
                    size=10, color=MUTED,
                ),
            ], spacing=5),
            bgcolor=with_alpha(ORANGE, 0.05),
            border=ft.border.all(1, with_alpha(ORANGE, 0.2)),
            border_radius=8, padding=10,
        )

        dlg = ft.AlertDialog(
            modal=True,
            title=ft.Row([
                ft.Icon(ft.Icons.PERSON_ROUNDED, color=GREEN, size=20),
                ft.Text("Cuenta de iRacing",
                        size=15, weight=ft.FontWeight.W_700, color=TEXT),
            ], spacing=10),
            content=ft.Container(
                content=ft.Column([
                    info_normal,
                    ft.Container(height=10),
                    user_field,
                    ft.Container(height=6),
                    pass_field,
                    ft.Container(height=14),
                    info_2fa,
                    ft.Container(height=10),
                    cookie_field,
                ], spacing=0),
                width=460,
            ),
            actions=[
                ft.TextButton("Cancelar",
                              style=ft.ButtonStyle(color=MUTED),
                              on_click=lambda e: self.page.close(dlg)),
                ft.ElevatedButton("Guardar",
                                  bgcolor=GREEN,
                                  style=ft.ButtonStyle(color="white"),
                                  on_click=save_creds),
            ],
            actions_alignment=ft.MainAxisAlignment.END,
            bgcolor=SURFACE,
            shape=ft.RoundedRectangleBorder(radius=16),
        )
        self.page.open(dlg)

    # ─── Sync ─────────────────────────────────────────────────────────────────
    def _do_sync(self, status_ref: ft.Ref):
        def _setup_path():
            if CAREER_BASE in sys.path:
                sys.path.remove(CAREER_BASE)
            sys.path.insert(0, CAREER_BASE)
            for key in list(sys.modules.keys()):
                if key.split(".")[0] in {"core", "data", "iracing"}:
                    del sys.modules[key]
            for k, v in _read_env().items():
                if v:
                    os.environ[k] = v

        def _run_engine():
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            async def sync():
                from core.career_engine import CareerEngine
                engine = CareerEngine()
                await engine.initialize()
                return await engine.login_and_sync()
            result = loop.run_until_complete(sync())
            loop.close()
            return result

        def _finish_ok(result):
            self._career_data = result
            self._is_demo = False
            status_ref.current.value = "Sincronizado ✓"
            status_ref.current.color = GREEN
            self.page.update()
            self._show_toast("✅ Carrera sincronizada con iRacing")

        def _finish_err(ex):
            error_detail = tb.format_exc()
            error_msg    = str(ex) if str(ex) else type(ex).__name__
            get_logger().log(source="iR Career · Sincronizar",
                             message=error_msg, detail=error_detail)
            status_ref.current.value = "Error — ver consola"
            status_ref.current.color = DANGER
            self.page.update()
            self._show_toast(
                f"❌ {error_msg[:70]}{'…' if len(error_msg) > 70 else ''}",
                color=DANGER,
            )

        def run():
            try:
                _setup_path()

                status_ref.current.value = "Conectando..."
                status_ref.current.color = WARNING
                self.page.update()

                result = _run_engine()
                _finish_ok(result)

            except Exception as ex:
                if "__NEEDS_2FA__" in str(ex):
                    # iRacing pidió 2FA — mostrar diálogo en el hilo de UI
                    self.page.run_task(self._show_2fa_dialog, status_ref)
                else:
                    _finish_err(ex)

        threading.Thread(target=run, daemon=True).start()

    # ─── Diálogo 2FA ──────────────────────────────────────────────────────────
    async def _show_2fa_dialog(self, status_ref: ft.Ref):
        import importlib
        env_data = _read_env()
        username = env_data.get("IRACING_USERNAME", "")
        password = env_data.get("IRACING_PASSWORD", "")

        code_field = ft.TextField(
            label="Código de verificación",
            hint_text="Código de 6 dígitos enviado a tu email",
            text_align=ft.TextAlign.CENTER,
            border_color=GREEN, focused_border_color=GREEN,
            text_size=20, max_length=6,
            keyboard_type=ft.KeyboardType.NUMBER,
            expand=True,
        )
        error_ref = ft.Ref[ft.Text]()

        def verify(e):
            code = code_field.value.strip()
            if len(code) < 4:
                error_ref.current.value = "Introduce el código completo"
                error_ref.current.visible = True
                self.page.update()
                return

            # Importar submit_2fa desde el módulo ya cargado
            if CAREER_BASE not in sys.path:
                sys.path.insert(0, CAREER_BASE)
            from iracing.client import submit_2fa
            result = submit_2fa(username, password, code)

            if result.get("ok"):
                self.page.close(dlg)
                status_ref.current.value = "Verificado, sincronizando..."
                status_ref.current.color = WARNING
                self.page.update()
                # Continuar con el sync
                def continue_sync():
                    try:
                        loop = asyncio.new_event_loop()
                        asyncio.set_event_loop(loop)
                        async def sync():
                            from core.career_engine import CareerEngine
                            engine = CareerEngine()
                            await engine.initialize()
                            return await engine.login_and_sync()
                        res = loop.run_until_complete(sync())
                        loop.close()
                        self._career_data = res
                        self._is_demo = False
                        status_ref.current.value = "Sincronizado ✓"
                        status_ref.current.color = GREEN
                        self.page.update()
                        self._show_toast("✅ Carrera sincronizada con iRacing")
                    except Exception as ex2:
                        status_ref.current.value = "Error — ver consola"
                        status_ref.current.color = DANGER
                        self.page.update()
                        self._show_toast(f"❌ {str(ex2)[:70]}", color=DANGER)
                threading.Thread(target=continue_sync, daemon=True).start()
            else:
                error_ref.current.value = result.get("error", "Código incorrecto")
                error_ref.current.visible = True
                self.page.update()

        dlg = ft.AlertDialog(
            modal=True,
            title=ft.Row([
                ft.Icon(ft.Icons.SHIELD_OUTLINED, color=GREEN, size=20),
                ft.Text("Verificación en dos pasos",
                        size=15, weight=ft.FontWeight.W_700, color=TEXT),
            ], spacing=10),
            content=ft.Container(
                content=ft.Column([
                    ft.Container(
                        content=ft.Row([
                            ft.Icon(ft.Icons.EMAIL_OUTLINED, color=CYAN, size=14),
                            ft.Text(
                                f"iRacing ha enviado un código de 6 dígitos\na {username}",
                                size=12, color=MUTED, expand=True,
                            ),
                        ], spacing=8),
                        bgcolor=with_alpha(CYAN, 0.05),
                        border=ft.border.all(1, with_alpha(CYAN, 0.15)),
                        border_radius=8, padding=12,
                    ),
                    ft.Container(height=16),
                    code_field,
                    ft.Container(height=6),
                    ft.Text(ref=error_ref, value="", color=DANGER,
                            size=11, visible=False),
                ], spacing=0),
                width=360,
            ),
            actions=[
                ft.TextButton("Cancelar",
                              style=ft.ButtonStyle(color=MUTED),
                              on_click=lambda e: self.page.close(dlg)),
                ft.ElevatedButton("Verificar",
                                  bgcolor=GREEN,
                                  style=ft.ButtonStyle(color="white"),
                                  on_click=verify),
            ],
            actions_alignment=ft.MainAxisAlignment.END,
            bgcolor=SURFACE,
            shape=ft.RoundedRectangleBorder(radius=16),
        )
        status_ref.current.value = "Esperando código 2FA..."
        status_ref.current.color = ORANGE
        self.page.update()
        self.page.open(dlg)

    def _show_toast(self, message: str, color: str = GREEN):
        self.page.snack_bar = ft.SnackBar(
            content=ft.Text(message, color="white"),
            bgcolor=color,
            behavior=ft.SnackBarBehavior.FLOATING,
            shape=ft.RoundedRectangleBorder(radius=10),
            margin=ft.margin.all(20),
            duration=2500,
        )
        self.page.snack_bar.open = True

    # ─── Perfil tab ───────────────────────────────────────────────────────────
    def _build_profile_tab(self, data: dict) -> ft.Container:
        pilot  = data.get("pilot", {})
        stats  = data.get("stats", {})
        races  = data.get("recent_races", [])
        contract = data.get("active_contract")

        # ── Datos del piloto ─────────────────────────────────────────────────
        name      = pilot.get("name", "Demo Piloto")
        balance   = pilot.get("balance", 0) or 0
        rep       = pilot.get("reputation", 50) or 50
        irating   = stats.get("irating", 0) or 0
        sr        = stats.get("safety_rating", 0) or 0
        lic       = stats.get("license_class", "R") or "R"
        category  = stats.get("category", "Road") or "Road"

        total_races = len(races)
        wins    = sum(1 for r in races if (r.get("finish_position") or 99) == 1)
        podiums = sum(1 for r in races if 0 < (r.get("finish_position") or 99) <= 3)
        avg_inc = (sum(r.get("incidents", 0) or 0 for r in races) / max(total_races, 1))
        best_pos = min((r.get("finish_position") or 99 for r in races), default=99)
        total_earned = sum(r.get("prize_money", 0) or 0 for r in races)

        # ── Colores de licencia ────────────────────────────────────────────────
        lic_colors = {"R": MUTED2, "D": WARNING, "C": ORANGE, "B": INFO, "A": GREEN, "Pro": PURPLE}
        lic_color  = lic_colors.get(lic, MUTED2)

        # ─────────────────────────────────────────────────────────────────────
        # CARD: Tarjeta de piloto
        # ─────────────────────────────────────────────────────────────────────
        initials = "".join(p[0].upper() for p in name.split()[:2]) or "FP"

        avatar = ft.Container(
            content=ft.Stack([
                ft.Container(
                    width=90, height=90,
                    border_radius=45,
                    gradient=ft.LinearGradient(
                        begin=ft.Alignment(-1, -1),
                        end=ft.Alignment(1, 1),
                        colors=[with_alpha(GREEN, 0.4), with_alpha(CYAN, 0.3)],
                    ),
                ),
                ft.Container(
                    content=ft.Text(initials, size=28, weight=ft.FontWeight.W_900, color=TEXT),
                    width=90, height=90,
                    alignment=ft.Alignment(0, 0),
                ),
            ]),
        )

        lic_badge = ft.Container(
            content=ft.Text(lic, size=12, color="white", weight=ft.FontWeight.W_900),
            bgcolor=lic_color,
            border_radius=8,
            padding=ft.padding.symmetric(horizontal=12, vertical=5),
        )

        rep_bar = ft.Column([
            ft.Row([
                ft.Text("Reputación", size=10, color=MUTED),
                ft.Text(f"{rep}/100", size=10, color=GREEN if rep >= 60 else WARNING,
                        weight=ft.FontWeight.W_700),
            ], alignment=ft.MainAxisAlignment.SPACE_BETWEEN),
            ft.ProgressBar(
                value=rep / 100,
                color=GREEN if rep >= 60 else (WARNING if rep >= 30 else DANGER),
                bgcolor=SURFACE3, height=6, border_radius=3,
            ),
        ], spacing=5)

        pilot_card = ft.Container(
            content=ft.Row([
                avatar,
                ft.Container(width=20),
                ft.Column([
                    ft.Row([
                        ft.Text(name, size=20, weight=ft.FontWeight.W_800, color=TEXT),
                        lic_badge,
                    ], spacing=10),
                    ft.Text(f"Categoría: {category}", size=11, color=MUTED),
                    ft.Container(height=10),
                    ft.Row([
                        self._stat_pill("📈", "iRating", str(irating) if irating else "---", GREEN),
                        self._stat_pill("🛡️", "SR",      f"{sr:.2f}" if sr else "---",       CYAN),
                        self._stat_pill("💰", "Balance",  f"${balance:,.0f}",                GREEN),
                    ], spacing=8),
                    ft.Container(height=10),
                    rep_bar,
                ], spacing=4, expand=True),
            ], spacing=0),
            bgcolor=SURFACE2,
            border_radius=18,
            border=ft.border.all(1, with_alpha(GREEN, 0.25)),
            padding=ft.padding.symmetric(horizontal=24, vertical=20),
            gradient=ft.LinearGradient(
                begin=ft.Alignment(-1, -1),
                end=ft.Alignment(1, 1),
                colors=[with_alpha(GREEN, 0.06), with_alpha(CYAN, 0.03)],
            ),
        )

        # ─────────────────────────────────────────────────────────────────────
        # LOGROS / CAREER STATS
        # ─────────────────────────────────────────────────────────────────────
        achiev_items = [
            ("🏁", "Carreras",      str(total_races), ORANGE),
            ("🥇", "Victorias",     str(wins),         WARNING),
            ("🏅", "Podios",        str(podiums),      CYAN),
            ("💵", "Ganancias",     f"${total_earned:,.0f}", GREEN),
            ("⚠️", "Inc. media",    f"{avg_inc:.1f}",  DANGER if avg_inc > 3 else MUTED),
            ("🎯", "Mejor pos.",    f"P{best_pos}" if best_pos < 99 else "---", GREEN),
        ]

        achievements_grid = ft.Row([
            self._achiev_card(*a) for a in achiev_items
        ], spacing=10, wrap=True)

        # ─────────────────────────────────────────────────────────────────────
        # POSESIONES (items comprados en tienda)
        # ─────────────────────────────────────────────────────────────────────
        owned_db = _qa("SELECT item_name, price_paid, bought_at FROM owned_item WHERE pilot_id=1 ORDER BY bought_at DESC")

        # Demo items si no hay datos reales
        demo_items = [
            {"item_name": "Mejora de setup básico", "price_paid": 2000, "icon": "🔧",
             "desc": "Aerodinámica base mejorada"},
            {"item_name": "Data engineer",          "price_paid": 5000, "icon": "📊",
             "desc": "+5% consistencia en vuelta"},
            {"item_name": "Simulador avanzado",      "price_paid": 8000, "icon": "🖥️",
             "desc": "Practica antes de la carrera"},
        ]

        if not owned_db and self._is_demo:
            items_to_show = demo_items
        else:
            # Enriquecer datos reales con iconos del catálogo
            icon_map = {
                "Mejora de setup básico": ("🔧", "Aerodinámica base mejorada"),
                "Data engineer":          ("📊", "+5% consistencia en vuelta"),
                "Simulador avanzado":     ("🖥️", "Practica antes de la carrera"),
                "Nutricionista":          ("🥗", "Mejora la concentración"),
                "Mecánico elite":         ("⚙️", "Pit stops más rápidos"),
                "Windtunnel session":     ("💨", "Optimización aerodinámica"),
            }
            items_to_show = []
            for row in owned_db:
                icon_e, desc = icon_map.get(row.get("item_name", ""), ("📦", "Ítem de carrera"))
                items_to_show.append({
                    "item_name":  row.get("item_name", "Ítem"),
                    "price_paid": row.get("price_paid", 0),
                    "icon":       icon_e,
                    "desc":       desc,
                })

        if items_to_show:
            items_grid = ft.Row([
                self._possession_card(
                    it.get("icon", "📦"),
                    it.get("item_name", "Ítem"),
                    it.get("desc", ""),
                    it.get("price_paid", 0),
                ) for it in items_to_show
            ], spacing=10, wrap=True)
        else:
            items_grid = ft.Container(
                content=ft.Column([
                    ft.Text("🛒", size=36, text_align=ft.TextAlign.CENTER),
                    ft.Text("Sin posesiones aún", size=13, color=MUTED,
                            text_align=ft.TextAlign.CENTER),
                    ft.Text("Ve a la Tienda para equiparte", size=11, color=MUTED2,
                            text_align=ft.TextAlign.CENTER),
                ], horizontal_alignment=ft.CrossAxisAlignment.CENTER, spacing=6),
                padding=ft.padding.symmetric(vertical=24),
                alignment=ft.Alignment(0, 0),
            )

        possessions_section = ft.Container(
            content=ft.Column([
                self._section_header("📦 Posesiones", "Ítems comprados en la tienda", CYAN),
                ft.Container(height=12),
                items_grid,
            ], spacing=0),
            bgcolor=SURFACE,
            border_radius=16,
            border=ft.border.all(1, with_alpha(CYAN, 0.15)),
            padding=ft.padding.symmetric(horizontal=18, vertical=16),
        )

        # ─────────────────────────────────────────────────────────────────────
        # STAFF
        # ─────────────────────────────────────────────────────────────────────
        staff_db = _qa("SELECT staff_type, name, monthly_cost, benefit_type, benefit_value FROM staff WHERE pilot_id=1 AND active=1")

        demo_staff = [
            {"staff_type": "Ingeniero",   "name": "Carlos R.",  "monthly_cost": 3500,
             "benefit_type": "Consistencia", "benefit_value": 5},
            {"staff_type": "Mecánico",    "name": "Miguel T.",  "monthly_cost": 2500,
             "benefit_type": "Pit stops",   "benefit_value": 10},
        ]
        staff_to_show = staff_db if staff_db else (demo_staff if self._is_demo else [])

        staff_icon_map = {
            "Ingeniero":    "👨‍💻",
            "Mecánico":     "🔩",
            "Nutricionista":"🥗",
            "Médico":       "🩺",
            "Data engineer":"📊",
            "Manager":      "👔",
        }

        if staff_to_show:
            staff_list = ft.Column([
                self._staff_card(
                    staff_icon_map.get(s.get("staff_type", ""), "👤"),
                    s.get("staff_type", "Staff"),
                    s.get("name", "---"),
                    s.get("monthly_cost", 0),
                    s.get("benefit_type", ""),
                    s.get("benefit_value", 0),
                ) for s in staff_to_show
            ], spacing=8)
        else:
            staff_list = ft.Container(
                content=ft.Text("Sin staff contratado. Ve a la Tienda.",
                                size=12, color=MUTED, text_align=ft.TextAlign.CENTER),
                padding=ft.padding.symmetric(vertical=20),
                alignment=ft.Alignment(0, 0),
            )

        staff_section = ft.Container(
            content=ft.Column([
                self._section_header("👥 Staff", "Personal contratado en tu equipo", PURPLE),
                ft.Container(height=12),
                staff_list,
            ], spacing=0),
            bgcolor=SURFACE,
            border_radius=16,
            border=ft.border.all(1, with_alpha(PURPLE, 0.15)),
            padding=ft.padding.symmetric(horizontal=18, vertical=16),
        )

        # ─────────────────────────────────────────────────────────────────────
        # CONTRATO ACTIVO
        # ─────────────────────────────────────────────────────────────────────
        if contract:
            contract_widget = self._contract_badge(contract)
        else:
            demo_contract = {
                "name": "Pro Circuit Racing",
                "salary_per_race": 2800,
                "tier": 3,
            } if self._is_demo else None
            contract_widget = self._contract_badge(demo_contract) if demo_contract else \
                ft.Container(
                    content=ft.Text("Sin contrato activo", size=12, color=MUTED,
                                    text_align=ft.TextAlign.CENTER),
                    padding=ft.padding.symmetric(vertical=14),
                    alignment=ft.Alignment(0, 0),
                )

        contract_section = ft.Container(
            content=ft.Column([
                self._section_header("📋 Contrato activo", "Tu acuerdo con el equipo actual", GREEN),
                ft.Container(height=12),
                contract_widget,
            ], spacing=0),
            bgcolor=SURFACE,
            border_radius=16,
            border=ft.border.all(1, with_alpha(GREEN, 0.15)),
            padding=ft.padding.symmetric(horizontal=18, vertical=16),
        )

        # ─────────────────────────────────────────────────────────────────────
        # LAYOUT FINAL
        # ─────────────────────────────────────────────────────────────────────
        return ft.Container(
            content=ft.Column([
                ft.Container(height=14),
                pilot_card,
                ft.Container(height=14),

                # Stats rápidas
                ft.Container(
                    content=ft.Column([
                        self._section_header("🏆 Estadísticas de carrera",
                                             "Resumen de tu rendimiento", ORANGE),
                        ft.Container(height=12),
                        achievements_grid,
                    ], spacing=0),
                    bgcolor=SURFACE,
                    border_radius=16,
                    border=ft.border.all(1, with_alpha(ORANGE, 0.15)),
                    padding=ft.padding.symmetric(horizontal=18, vertical=16),
                ),
                ft.Container(height=12),

                # Fila inferior: posesiones + staff + contrato
                ft.Row([
                    ft.Column([possessions_section], expand=True, spacing=0),
                    ft.Container(width=12),
                    ft.Column([staff_section, ft.Container(height=12), contract_section],
                              expand=True, spacing=0),
                ], spacing=0, expand=True),
                ft.Container(height=14),
            ], spacing=0, scroll=ft.ScrollMode.AUTO, expand=True),
            expand=True,
        )

    # ── Helpers del Perfil ────────────────────────────────────────────────────
    def _stat_pill(self, emoji: str, label: str, value: str, accent: str) -> ft.Container:
        return ft.Container(
            content=ft.Column([
                ft.Row([
                    ft.Text(emoji, size=12),
                    ft.Text(value, size=14, weight=ft.FontWeight.W_800, color=TEXT),
                ], spacing=4),
                ft.Text(label, size=9, color=MUTED),
            ], spacing=2, horizontal_alignment=ft.CrossAxisAlignment.CENTER),
            bgcolor=with_alpha(accent, 0.08),
            border=ft.border.all(1, with_alpha(accent, 0.2)),
            border_radius=12,
            padding=ft.padding.symmetric(horizontal=14, vertical=8),
        )

    def _achiev_card(self, emoji: str, label: str, value: str, accent: str) -> ft.Container:
        return ft.Container(
            content=ft.Column([
                ft.Text(emoji, size=20, text_align=ft.TextAlign.CENTER),
                ft.Text(value, size=18, weight=ft.FontWeight.W_800,
                        color=accent, text_align=ft.TextAlign.CENTER),
                ft.Text(label, size=9, color=MUTED, text_align=ft.TextAlign.CENTER),
            ], spacing=4, horizontal_alignment=ft.CrossAxisAlignment.CENTER),
            bgcolor=SURFACE2,
            border_radius=14,
            border=ft.border.all(1, with_alpha(accent, 0.18)),
            padding=ft.padding.symmetric(horizontal=16, vertical=14),
            width=110,
            alignment=ft.Alignment(0, 0),
        )

    def _possession_card(self, emoji: str, name: str, desc: str, price: float) -> ft.Container:
        return ft.Container(
            content=ft.Column([
                ft.Row([
                    ft.Container(
                        content=ft.Text(emoji, size=20),
                        width=42, height=42,
                        bgcolor=with_alpha(CYAN, 0.1),
                        border_radius=12,
                        alignment=ft.Alignment(0, 0),
                    ),
                    ft.Column([
                        ft.Text(name, size=12, weight=ft.FontWeight.W_700, color=TEXT),
                        ft.Text(desc, size=10, color=MUTED),
                    ], spacing=2, expand=True),
                ], spacing=10),
                ft.Container(height=8),
                ft.Row([
                    ft.Text("Pagado:", size=10, color=MUTED),
                    ft.Text(f"${price:,.0f}", size=11, color=CYAN,
                            weight=ft.FontWeight.W_700),
                ], spacing=6),
            ], spacing=0),
            bgcolor=SURFACE2,
            border_radius=14,
            border=ft.border.all(1, with_alpha(CYAN, 0.15)),
            padding=ft.padding.symmetric(horizontal=14, vertical=12),
            width=220,
        )

    def _staff_card(self, emoji: str, role: str, name: str,
                    cost: float, benefit: str, benefit_val: float) -> ft.Container:
        return ft.Container(
            content=ft.Row([
                ft.Container(
                    content=ft.Text(emoji, size=18),
                    width=40, height=40,
                    bgcolor=with_alpha(PURPLE, 0.1),
                    border_radius=10,
                    alignment=ft.Alignment(0, 0),
                ),
                ft.Column([
                    ft.Row([
                        ft.Text(name, size=12, weight=ft.FontWeight.W_700, color=TEXT),
                        ft.Container(
                            content=ft.Text(role, size=9, color=PURPLE,
                                            weight=ft.FontWeight.W_600),
                            bgcolor=with_alpha(PURPLE, 0.1),
                            border_radius=6,
                            padding=ft.padding.symmetric(horizontal=7, vertical=2),
                        ),
                    ], spacing=6),
                    ft.Row([
                        ft.Text(f"${cost:,.0f}/mes", size=10, color=MUTED),
                        ft.Text("·", size=10, color=MUTED2),
                        ft.Text(f"{benefit}: +{benefit_val}%", size=10, color=GREEN),
                    ], spacing=4),
                ], spacing=3, expand=True),
            ], spacing=10),
            bgcolor=SURFACE2,
            border_radius=12,
            border=ft.border.all(1, with_alpha(PURPLE, 0.15)),
            padding=ft.padding.symmetric(horizontal=12, vertical=10),
        )

    def _contract_badge(self, contract: dict) -> ft.Container:
        if not contract:
            return ft.Container()
        tier_colors = {1: MUTED, 2: GREEN, 3: ORANGE, 4: PURPLE}
        tier_labels = {1: "Tier 1 — Rookie", 2: "Tier 2 — Amateur",
                       3: "Tier 3 — Pro", 4: "Tier 4 — Elite"}
        tier   = contract.get("tier", 1)
        accent = tier_colors.get(tier, GREEN)

        return ft.Container(
            content=ft.Row([
                ft.Container(
                    content=ft.Text("📋", size=22),
                    width=48, height=48,
                    bgcolor=with_alpha(accent, 0.12),
                    border_radius=14,
                    alignment=ft.Alignment(0, 0),
                ),
                ft.Column([
                    ft.Text(contract.get("name", "Equipo"), size=14,
                            weight=ft.FontWeight.W_800, color=TEXT),
                    ft.Text(tier_labels.get(tier, "Tier 1"), size=10,
                            color=accent, weight=ft.FontWeight.W_600),
                    ft.Text(f"Salario: ${contract.get('salary_per_race', 0):,.0f} / carrera",
                            size=11, color=MUTED),
                ], spacing=3, expand=True),
                ft.Container(
                    content=ft.Text("Activo", size=10, color="white",
                                    weight=ft.FontWeight.W_700),
                    bgcolor=with_alpha(accent, 0.85),
                    border_radius=10,
                    padding=ft.padding.symmetric(horizontal=10, vertical=4),
                ),
            ], spacing=12),
            bgcolor=with_alpha(accent, 0.06),
            border_radius=14,
            border=ft.border.all(1, with_alpha(accent, 0.25)),
            padding=ft.padding.symmetric(horizontal=16, vertical=14),
        )

    def _section_header(self, title: str, subtitle: str, accent: str) -> ft.Row:
        return ft.Row([
            ft.Container(width=3, height=18, bgcolor=accent, border_radius=2),
            ft.Column([
                ft.Text(title, size=13, weight=ft.FontWeight.W_700, color=TEXT),
                ft.Text(subtitle, size=10, color=MUTED),
            ], spacing=1, expand=True),
        ], spacing=10)
        self.page.update()
