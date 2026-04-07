# ui/views/settings_view.py
# Vista de Ajustes — FanTan Hub

import flet as ft
import os
import json
from ui.colors import *
from ui.components import *


BASE = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
BOT_CONFIG   = os.path.join(BASE, "bot_twitch", "config.json")
TRACKER_ENV  = os.path.join(BASE, "iracing_tracker", ".env")
CAREER_ENV   = os.path.join(BASE, "iracing_career", ".env.example")


class SettingsView:
    def __init__(self, state: dict, page: ft.Page):
        self.state = state
        self.page = page

    # ─── Build ────────────────────────────────────────────────────────────────
    def build(self) -> ft.Control:
        header = module_header(
            "⚙️", "Ajustes",
            subtitle="Configuración general de FanTan Hub",
            accent=CYAN,
        )

        # ─── Sección Bot Twitch ───────────────────────────────────────────────
        bot_config_exists = os.path.exists(BOT_CONFIG)
        bot_section = self._build_section(
            "🟣 Bot de Twitch",
            "Configura las credenciales y opciones del bot",
            PURPLE,
            [
                self._info_item(
                    "Archivo de configuración",
                    "config.json",
                    "✅ Encontrado" if bot_config_exists else "❌ No encontrado",
                    SUCCESS if bot_config_exists else DANGER,
                ),
                self._info_item(
                    "Ruta",
                    os.path.relpath(BOT_CONFIG, BASE),
                    "",
                    MUTED,
                ),
                ft.Container(height=8),
                ft.Container(
                    content=ft.Row([
                        ft.Icon(ft.Icons.INFO_OUTLINE_ROUNDED, color=PURPLE, size=14),
                        ft.Text(
                            "Edita app/bot_twitch/config.json para configurar tokens y opciones del bot.",
                            size=12, color=MUTED, expand=True,
                        ),
                    ], spacing=8),
                    bgcolor=with_alpha(PURPLE, 0.06),
                    border=ft.border.all(1, with_alpha(PURPLE, 0.2)),
                    border_radius=8,
                    padding=10,
                ),
            ],
        )

        # ─── Sección iRacing Tracker ──────────────────────────────────────────
        tracker_env_exists = os.path.exists(TRACKER_ENV)
        tracker_section = self._build_section(
            "🏎️ iRacing Tracker",
            "Credenciales de iRacing para el tracker",
            ORANGE,
            [
                self._info_item(
                    "Archivo de entorno",
                    ".env",
                    "✅ Encontrado" if tracker_env_exists else "❌ No encontrado",
                    SUCCESS if tracker_env_exists else DANGER,
                ),
                self._info_item(
                    "Ruta",
                    os.path.relpath(TRACKER_ENV, BASE),
                    "",
                    MUTED,
                ),
                ft.Container(height=8),
                ft.Container(
                    content=ft.Row([
                        ft.Icon(ft.Icons.INFO_OUTLINE_ROUNDED, color=ORANGE, size=14),
                        ft.Text(
                            "Edita app/iracing_tracker/.env con tu usuario y contraseña de iRacing.",
                            size=12, color=MUTED, expand=True,
                        ),
                    ], spacing=8),
                    bgcolor=with_alpha(ORANGE, 0.06),
                    border=ft.border.all(1, with_alpha(ORANGE, 0.2)),
                    border_radius=8,
                    padding=10,
                ),
            ],
        )

        # ─── Sección iRacing Career ───────────────────────────────────────────
        career_section = self._build_section(
            "🏆 iRacing Career",
            "Configuración del modo carrera virtual",
            GREEN,
            [
                self._info_item(
                    "Archivo de entorno",
                    ".env",
                    "Usa .env.example como plantilla",
                    MUTED,
                ),
                self._info_item(
                    "Ruta",
                    os.path.relpath(CAREER_ENV, BASE),
                    "",
                    MUTED,
                ),
                ft.Container(height=8),
                ft.Container(
                    content=ft.Row([
                        ft.Icon(ft.Icons.INFO_OUTLINE_ROUNDED, color=GREEN, size=14),
                        ft.Text(
                            "Copia .env.example a .env en app/iracing_career/ y rellena tus credenciales.",
                            size=12, color=MUTED, expand=True,
                        ),
                    ], spacing=8),
                    bgcolor=with_alpha(GREEN, 0.06),
                    border=ft.border.all(1, with_alpha(GREEN, 0.2)),
                    border_radius=8,
                    padding=10,
                ),
            ],
        )

        # ─── Sección Info del hub ─────────────────────────────────────────────
        hub_section = self._build_section(
            "ℹ️ Información",
            "Estado actual del FanTan Hub",
            CYAN,
            [
                self._info_item("Versión", "FanTan Hub v1.0", "", TEXT),
                self._info_item("Bot", "Online" if self.state.get("bot_running") else "Offline",
                                "", SUCCESS if self.state.get("bot_running") else DANGER),
                self._info_item("Tracker", "Online" if self.state.get("tracker_running") else "Offline",
                                "", SUCCESS if self.state.get("tracker_running") else DANGER),
                self._info_item("Directorio base", os.path.basename(BASE), "", MUTED),
            ],
        )

        return ft.Column([
            header,
            ft.Container(height=20),
            ft.Column([
                ft.Row([
                    ft.Column([bot_section, ft.Container(height=16), tracker_section], spacing=0, expand=True),
                    ft.Container(width=16),
                    ft.Column([career_section, ft.Container(height=16), hub_section], spacing=0, expand=True),
                ], spacing=0, expand=True),
            ], spacing=0, scroll=ft.ScrollMode.AUTO, expand=True),
        ], spacing=0, expand=True)

    # ─── Helpers ──────────────────────────────────────────────────────────────
    def _build_section(self, title: str, subtitle: str, accent: str, controls: list) -> ft.Container:
        return ft.Container(
            content=ft.Column([
                ft.Row([
                    ft.Container(width=3, height=18, bgcolor=accent, border_radius=2),
                    ft.Column([
                        ft.Text(title, size=14, weight=ft.FontWeight.W_700, color=TEXT),
                        ft.Text(subtitle, size=11, color=MUTED),
                    ], spacing=1, expand=True),
                ], spacing=10),
                ft.Container(height=12),
                *controls,
            ], spacing=4),
            bgcolor=SURFACE,
            border_radius=14,
            border=ft.border.all(1, with_alpha(accent, 0.18)),
            padding=ft.padding.symmetric(horizontal=16, vertical=14),
        )

    def _info_item(self, label: str, value: str, extra: str, value_color: str) -> ft.Container:
        right_items = [ft.Text(value, size=12, color=value_color, weight=ft.FontWeight.W_500)]
        if extra:
            right_items.append(ft.Text(extra, size=11, color=value_color))
        return ft.Container(
            content=ft.Row([
                ft.Text(label, size=12, color=MUTED, expand=True),
                ft.Column(right_items, spacing=2, horizontal_alignment=ft.CrossAxisAlignment.END),
            ]),
            padding=ft.padding.symmetric(vertical=4),
        )
