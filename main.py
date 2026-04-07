#!/usr/bin/env python3
"""
FanTan Hub — Aplicación unificada
Twitch Bot · iRacing Tracker · iRacing Career

Ejecutar:  python main.py
"""

import flet as ft
import os
import sys

# Añadir el directorio raíz al path para importar módulos hermanos
CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
if CURRENT_DIR not in sys.path:
    sys.path.insert(0, CURRENT_DIR)

from ui.colors import *
from ui.sidebar import Sidebar
from ui.error_logger import get_logger
from ui.views.home_view     import HomeView
from ui.views.twitch_view   import TwitchView
from ui.views.tracker_view  import TrackerView
from ui.views.career_view   import CareerView
from ui.views.settings_view import SettingsView


# ─── Aplicación principal ─────────────────────────────────────────────────────
class FanTanHub:
    def __init__(self, page: ft.Page):
        self.page = page
        self.current_view = "home"
        self.content_area = ft.Container(expand=True)

        # Estado compartido entre vistas
        self.state: dict = {
            "bot_running": False,
            "tracker_running": False,
            "_bot_instance": None,
            "_bot_thread": None,
            "_logger_instance": None,
            "_logger_thread": None,
        }

    # ─── Setup de página ──────────────────────────────────────────────────────
    def _setup_page(self):
        self.page.title = "FanTan Hub · Twitch + iRacing"
        self.page.theme_mode = ft.ThemeMode.DARK
        self.page.bgcolor = BG
        self.page.padding = 0
        self.page.spacing = 0
        self.page.window.width = 1280
        self.page.window.height = 820
        self.page.window.min_width = 1024
        self.page.window.min_height = 680
        self.page.window.title_bar_hidden = False
        self.page.fonts = {}
        self.page.theme = ft.Theme(
            color_scheme_seed=PURPLE,
            visual_density=ft.VisualDensity.COMPACT,
            font_family="Segoe UI",
        )

    # ─── Header superior ──────────────────────────────────────────────────────
    def _build_header(self) -> ft.Container:
        self._header_title_ref = ft.Ref[ft.Text]()
        self._header_sub_ref   = ft.Ref[ft.Text]()

        view_titles = {
            "home":     ("⚡ FanTan Hub",        "Dashboard principal"),
            "twitch":   ("🟣 Twitch Bot",         "Bot de Twitch — fantan"),
            "tracker":  ("🏎️ iRacing Tracker",   "Telemetría & estadísticas"),
            "career":   ("🏆 iRacing Career",     "Modo carrera virtual"),
            "settings": ("⚙️ Ajustes",            "Configuración general"),
        }

        self._view_titles = view_titles

        title, sub = view_titles.get("home")

        # Indicadores de estado
        self._bot_dot    = ft.Container(width=7, height=7, bgcolor=DANGER, border_radius=4)
        self._logger_dot = ft.Container(width=7, height=7, bgcolor=DANGER, border_radius=4)

        return ft.Container(
            content=ft.Row([
                # Breadcrumb
                ft.Column([
                    ft.Text(ref=self._header_title_ref, value=title,
                            size=15, weight=ft.FontWeight.W_700, color=TEXT),
                    ft.Text(ref=self._header_sub_ref, value=sub,
                            size=11, color=MUTED),
                ], spacing=1, expand=True),

                # Status badges
                ft.Row([
                    ft.Container(
                        content=ft.Row([
                            self._bot_dot,
                            ft.Text("Bot", size=11, color=MUTED),
                        ], spacing=5),
                        bgcolor=SURFACE2,
                        border=ft.border.all(1, BORDER2),
                        border_radius=8,
                        padding=ft.padding.symmetric(horizontal=10, vertical=5),
                        tooltip="Estado del Bot de Twitch",
                    ),
                    ft.Container(
                        content=ft.Row([
                            self._logger_dot,
                            ft.Text("Logger", size=11, color=MUTED),
                        ], spacing=5),
                        bgcolor=SURFACE2,
                        border=ft.border.all(1, BORDER2),
                        border_radius=8,
                        padding=ft.padding.symmetric(horizontal=10, vertical=5),
                        tooltip="Estado del iRacing Logger",
                    ),
                    ft.Container(
                        content=ft.Text("FanTan Hub v1.0", size=10, color=MUTED2),
                        padding=ft.padding.symmetric(horizontal=8, vertical=5),
                    ),
                ], spacing=8),
            ], spacing=0),
            bgcolor=SURFACE,
            border=ft.border.only(bottom=ft.BorderSide(1, BORDER2)),
            padding=ft.padding.symmetric(horizontal=22, vertical=12),
        )

    # ─── Navegación ───────────────────────────────────────────────────────────
    def _navigate(self, view_id: str):
        self.current_view = view_id
        self._update_header(view_id)
        self._load_view(view_id)
        self.page.update()

    def _update_header(self, view_id: str):
        title, sub = self._view_titles.get(view_id, ("FanTan Hub", ""))
        self._header_title_ref.current.value = title
        self._header_sub_ref.current.value   = sub

        # Actualizar dots
        self._bot_dot.bgcolor    = SUCCESS if self.state.get("bot_running")     else DANGER
        self._logger_dot.bgcolor = SUCCESS if self.state.get("tracker_running") else DANGER

    def _load_view(self, view_id: str):
        self.content_area.content = ft.Container(
            content=ft.Column([
                ft.ProgressRing(color=CYAN, width=28, height=28),
                ft.Text("Cargando...", size=12, color=MUTED),
            ], horizontal_alignment=ft.CrossAxisAlignment.CENTER,
               alignment=ft.MainAxisAlignment.CENTER),
            alignment=ft.Alignment(0, 0),
            expand=True,
        )
        self.page.update()

        views = {
            "home":     lambda: HomeView(self.state, self._navigate).build(),
            "twitch":   lambda: TwitchView(self.state, self.page).build(),
            "tracker":  lambda: TrackerView(self.state, self.page).build(),
            "career":   lambda: CareerView(self.state, self.page).build(),
            "settings": lambda: SettingsView(self.state, self.page).build(),
        }

        builder = views.get(view_id)
        if builder:
            try:
                self.content_area.content = ft.Container(
                    content=builder(),
                    expand=True,
                    padding=ft.padding.symmetric(horizontal=24, vertical=20),
                )
            except Exception as ex:
                self.content_area.content = ft.Container(
                    content=ft.Column([
                        ft.Text("⚠️", size=48),
                        ft.Text(f"Error al cargar la vista", size=16, color=DANGER),
                        ft.Text(str(ex), size=12, color=MUTED),
                    ], horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                       alignment=ft.MainAxisAlignment.CENTER),
                    alignment=ft.Alignment(0, 0),
                    expand=True,
                )

    # ─── Consola de errores ───────────────────────────────────────────────────
    def _open_error_console(self):
        """Abre la ventana flotante de consola de errores."""
        logger = get_logger()
        errors = logger.get_all()

        def _clear_and_close(e):
            logger.clear()
            self.page.close(dlg)

        # Construir filas de errores
        rows = []
        if not errors:
            rows.append(
                ft.Container(
                    content=ft.Column([
                        ft.Text("✅", size=36, text_align=ft.TextAlign.CENTER),
                        ft.Text("Sin errores registrados", size=14, color=MUTED,
                                text_align=ft.TextAlign.CENTER),
                    ], horizontal_alignment=ft.CrossAxisAlignment.CENTER, spacing=8),
                    alignment=ft.Alignment(0, 0),
                    height=120,
                )
            )
        else:
            for err in errors:
                detail_ref = ft.Ref[ft.Container]()
                detail_text = ft.Ref[ft.Text]()

                def toggle_detail(e, dr=detail_ref):
                    dr.current.visible = not dr.current.visible
                    try:
                        dr.current.update()
                    except Exception:
                        pass

                rows.append(
                    ft.Container(
                        content=ft.Column([
                            ft.Row([
                                ft.Container(
                                    content=ft.Text("⚠", size=13, color=DANGER),
                                    width=24, height=24,
                                    bgcolor=with_alpha(DANGER, 0.12),
                                    border_radius=6,
                                    alignment=ft.Alignment(0, 0),
                                ),
                                ft.Column([
                                    ft.Text(
                                        f"[{err['ts']}] {err['source']}",
                                        size=10, color=MUTED,
                                        weight=ft.FontWeight.W_500,
                                    ),
                                    ft.Text(
                                        err["message"],
                                        size=12, color=TEXT,
                                        weight=ft.FontWeight.W_600,
                                    ),
                                ], spacing=1, expand=True),
                                ft.TextButton(
                                    "detalle",
                                    style=ft.ButtonStyle(
                                        color=MUTED,
                                        padding=ft.padding.symmetric(horizontal=6, vertical=2),
                                    ),
                                    on_click=toggle_detail,
                                ) if err.get("detail") else ft.Container(),
                            ], spacing=8),
                            ft.Container(
                                ref=detail_ref,
                                content=ft.Text(
                                    ref=detail_text,
                                    value=err.get("detail", ""),
                                    size=10,
                                    color=ORANGE_L,
                                    font_family="Consolas, monospace",
                                    selectable=True,
                                ),
                                bgcolor=with_alpha(ORANGE, 0.05),
                                border=ft.border.all(0.5, with_alpha(ORANGE, 0.2)),
                                border_radius=8,
                                padding=10,
                                visible=False,
                                margin=ft.margin.only(top=6),
                            ),
                        ], spacing=4),
                        bgcolor=SURFACE2,
                        border=ft.border.all(0.5, with_alpha(DANGER, 0.2)),
                        border_radius=10,
                        padding=12,
                        margin=ft.margin.only(bottom=8),
                    )
                )

        console_content = ft.Container(
            content=ft.Column(rows, spacing=0, scroll=ft.ScrollMode.AUTO),
            height=400,
        )

        dlg = ft.AlertDialog(
            modal=True,
            title=ft.Row([
                ft.Icon(ft.Icons.BUG_REPORT_ROUNDED, color=DANGER, size=20),
                ft.Text(
                    f"Consola de errores  ({len(errors)} entrada{'s' if len(errors) != 1 else ''})",
                    size=15, weight=ft.FontWeight.W_700, color=TEXT,
                ),
            ], spacing=10),
            content=ft.Container(
                content=ft.Column([
                    ft.Text(
                        "Errores capturados durante esta sesión. "
                        "Haz clic en 'detalle' para ver el traceback completo.",
                        size=11, color=MUTED,
                    ),
                    ft.Container(height=10),
                    console_content,
                ], spacing=0),
                width=640,
            ),
            actions=[
                ft.TextButton(
                    "Limpiar errores",
                    style=ft.ButtonStyle(color=DANGER),
                    on_click=_clear_and_close,
                ),
                ft.ElevatedButton(
                    "Cerrar",
                    bgcolor=SURFACE3,
                    style=ft.ButtonStyle(color=TEXT),
                    on_click=lambda e: self.page.close(dlg),
                ),
            ],
            actions_alignment=ft.MainAxisAlignment.END,
            bgcolor=SURFACE,
            shape=ft.RoundedRectangleBorder(radius=16),
        )

        self.page.open(dlg)

    # ─── Build principal ──────────────────────────────────────────────────────
    def run(self):
        self._setup_page()

        sidebar = Sidebar(
            on_nav=self._navigate,
            initial="home",
            on_open_console=self._open_error_console,
        )
        sidebar_ctrl = sidebar.build()

        header = self._build_header()

        layout = ft.Row([
            sidebar_ctrl,
            ft.Container(
                content=ft.Column([
                    header,
                    ft.Container(content=self.content_area, expand=True),
                ], spacing=0, expand=True),
                expand=True,
                bgcolor=BG,
            ),
        ], spacing=0, expand=True)

        self.page.add(layout)
        self._navigate("home")


# ─── Entry point ──────────────────────────────────────────────────────────────
def main(page: ft.Page):
    app = FanTanHub(page)
    app.run()


if __name__ == "__main__":
    ft.app(main)
