import flet as ft
from dotenv import load_dotenv
from core.career_engine import CareerEngine
from ui.views.dashboard import DashboardView
from ui.views.contracts import ContractsView
from ui.views.shop import ShopView
from ui.views.medical import MedicalView
from ui.views.incidents import IncidentsView

load_dotenv()

# Colores globales (estilo oscuro racing)
COLORS = {
    "bg":       "#0d0f14",
    "surface":  "#1a1d28",
    "surface2": "#12151c",
    "border":   "#ffffff12",
    "purple":   "#7F77DD",
    "purple_l": "#AFA9EC",
    "green":    "#5DCAA5",
    "amber":    "#EF9F27",
    "red":      "#E24B4A",
    "text":     "#e0ddf5",
    "muted":    "#7f7d90",
}


async def main(page: ft.Page):
    page.title = "iRacing Career Mode"
    page.theme_mode = ft.ThemeMode.DARK
    page.bgcolor = COLORS["bg"]
    page.padding = 0

    # FIX warnings flet (window_... deprecated)
    page.window.width = 1000
    page.window.height = 700
    page.window.min_width = 800
    page.window.min_height = 600

    engine = CareerEngine()
    await engine.initialize()

    # Estado compartido entre vistas
    state = {"data": None, "current_view": "dashboard"}

    # Contenedor principal de la vista activa
    content_area = ft.Container(expand=True)

    # REF para actualizar el texto de estado de sincronización
    sync_status_ref = ft.Ref[ft.Text]()

    def switch_view(view_name: str):
        state["current_view"] = view_name

        views = {
            "dashboard": DashboardView(state["data"], COLORS, engine),
            "contracts": ContractsView(state["data"], COLORS, engine),
            "shop":      ShopView(state["data"], COLORS, engine),
            "medical":   MedicalView(state["data"], COLORS, engine),
            "incidents": IncidentsView(state["data"], COLORS, engine),
        }

        content_area.content = views[view_name].build()

        # Actualizar tab activo
        for btn in nav_buttons:
            btn.style = ft.ButtonStyle(
                color=COLORS["purple"] if btn.data == view_name else COLORS["muted"],
                padding=ft.padding.symmetric(vertical=8, horizontal=12),
            )

        page.update()

    def make_nav_btn(icon, label, view_name):
        btn = ft.TextButton(
            content=ft.Column(
                [ft.Icon(icon, size=18), ft.Text(label, size=9)],
                horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                spacing=2,
            ),
            style=ft.ButtonStyle(
                color=COLORS["purple"] if view_name == "dashboard" else COLORS["muted"],
                padding=ft.padding.symmetric(vertical=8, horizontal=12),
            ),
            on_click=lambda e, v=view_name: switch_view(v),
            data=view_name,
        )
        return btn

    nav_buttons = [
        make_nav_btn(ft.Icons.DASHBOARD_OUTLINED, "Dashboard", "dashboard"),
        make_nav_btn(ft.Icons.DESCRIPTION_OUTLINED, "Contratos", "contracts"),
        make_nav_btn(ft.Icons.STOREFRONT_OUTLINED, "Tienda", "shop"),
        make_nav_btn(ft.Icons.MEDICAL_SERVICES_OUTLINED, "Médico", "medical"),
        make_nav_btn(ft.Icons.WARNING_AMBER_OUTLINED, "Incidentes", "incidents"),
    ]

    # Barra superior
    topbar = ft.Container(
        content=ft.Row(
            [
                ft.Row(
                    [
                        ft.Icon(ft.Icons.SPEED, color=COLORS["purple"], size=20),
                        ft.Column(
                            [
                                ft.Text(
                                    "iRacing Career",
                                    size=13,
                                    weight=ft.FontWeight.W_500,
                                    color=COLORS["text"],
                                ),
                                ft.Text(
                                    "Modo carrera",
                                    size=10,
                                    color=COLORS["purple"],
                                ),
                            ],
                            spacing=0,
                        ),
                    ],
                    spacing=8,
                ),
                ft.Row(nav_buttons, spacing=0),
                ft.Container(
                    content=ft.Text(
                        "Sincronizando...",
                        size=11,
                        color=COLORS["muted"],
                        ref=sync_status_ref,
                    ),
                ),
            ],
            alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
        ),
        bgcolor=COLORS["surface2"],
        border=ft.border.only(bottom=ft.BorderSide(0.5, COLORS["border"])),
        padding=ft.padding.symmetric(horizontal=16, vertical=8),
    )

    # Layout principal
    page.add(
        ft.Column(
            [
                topbar,
                ft.Container(content=content_area, expand=True, padding=14),
            ],
            spacing=0,
            expand=True,
        )
    )

    # Pantalla de carga inicial
    content_area.content = ft.Column(
        [
            ft.ProgressRing(color=COLORS["purple"]),
            ft.Text("Conectando con iRacing...", color=COLORS["muted"], size=13),
        ],
        alignment=ft.MainAxisAlignment.CENTER,
        horizontal_alignment=ft.CrossAxisAlignment.CENTER,
        expand=True,
    )
    page.update()

    # Sincronizar datos reales
    try:
        sync_status_ref.current.value = "Conectando a iRacing..."
        page.update()

        state["data"] = await engine.login_and_sync()

        sync_status_ref.current.value = "Conectado"
        sync_status_ref.current.color = COLORS["green"]
        page.update()

    except Exception:
        # Modo demo si no hay credenciales
        state["data"] = _demo_state()

        sync_status_ref.current.value = "Modo demo"
        sync_status_ref.current.color = COLORS["amber"]
        page.update()

    switch_view("dashboard")


def _demo_state() -> dict:
    """Estado de demo para probar sin credenciales de iRacing."""
    return {
        "pilot": {"id": 1, "name": "Demo Piloto", "balance": 48200, "reputation": 62},
        "stats": {
            "irating": 3842,
            "safety_rating": 4.72,
            "license_class": "A",
            "category": "Road",
        },
        "recent_races": [
            {
                "track": "Spa-Francorchamps",
                "finish_position": 1,
                "incidents": 0,
                "irating_change": 48,
                "sr_change": 0.12,
                "prize_money": 1800,
                "raced_at": "",
            },
            {
                "track": "Silverstone GP",
                "finish_position": 2,
                "incidents": 1,
                "irating_change": 22,
                "sr_change": 0.05,
                "prize_money": 900,
                "raced_at": "",
            },
            {
                "track": "Monza",
                "finish_position": 5,
                "incidents": 2,
                "irating_change": -8,
                "sr_change": -0.02,
                "prize_money": 350,
                "raced_at": "",
            },
            {
                "track": "Nürburgring",
                "finish_position": 99,
                "incidents": 8,
                "irating_change": -45,
                "sr_change": -0.18,
                "prize_money": -200,
                "raced_at": "",
            },
        ],
        "active_contract": None,
        "active_sanctions": [],
        "is_banned": False,
        "ban_reason": "",
        "contract_status": {},
    }


ft.app(target=main)