# gui/dashboard/tabs/settings_tab.py
import flet as ft
import json
import os
from gui.dashboard.tabs.base_tab import BaseTab
from gui.styles import AppColors
from core.database import db
from gui.dialogs.setup_dialog import SetupDialog

CURRENT_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
BASE_DIR = os.path.dirname(CURRENT_DIR)
CONFIG_PATH = os.path.join(BASE_DIR, "config.json")

class SettingsTab(BaseTab):
    def __init__(self, page: ft.Page):
        super().__init__(page)
        self.username_actual = self.page.session.get("username")
        self.config = self._load_config()
        self.user_tier = self._get_user_tier()

        if self.user_tier >= 3:
            db.migrate_admin_config(self.username_actual, self.config)

    def _get_user_tier(self):
        if not self.username_actual:
            return 0
        user = db.get_user(self.username_actual)
        return int(user["tier"]) if user else 0

    def _load_config(self):
        default = {
            "twitch": {
                "channel": "", "bot_name": "", "broadcaster_id": "",
                "token_bot": "", "client_id_bot": "", "token": "",
                "client_id": "", "client_secret": ""
            },
            "openai": {"api_key": ""},
            "admin_users": []
        }
        if os.path.exists(CONFIG_PATH):
            try:
                with open(CONFIG_PATH, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    if "twitch" in data:
                        default["twitch"].update(data["twitch"])
                    if "openai" in data:
                        default["openai"].update(data["openai"])
                    if "admin_users" in data:
                        default["admin_users"] = data["admin_users"]
            except:
                pass
        return default

    def _save_individual(self, key, subkey, value):
        if subkey:
            if key not in self.config:
                self.config[key] = {}
            self.config[key][subkey] = value
        else:
            if key == "admin_users":
                value = [u.strip() for u in value.split(",") if u.strip()]
            self.config[key] = value
        try:
            with open(CONFIG_PATH, "w", encoding="utf-8") as f:
                json.dump(self.config, f, indent=4)
            if key == "twitch" and subkey:
                db.save_user_config(username=self.username_actual, **{subkey: value})
            elif key == "openai" and subkey == "api_key":
                db.save_user_config(username=self.username_actual, openai_api_key=value)
            self._show_snackbar("✅ Guardado correctamente", ft.Colors.GREEN_700)
        except Exception as e:
            self._show_snackbar(f"❌ Error: {e}", ft.Colors.RED_700)

    def create_setting_field(self, label, value, config_key, sub_key=None):
        is_secret = any(x in label.lower() for x in ["key", "token", "secret", "id"])
        text_field = ft.TextField(
            label=label, value=str(value), height=45, text_size=12, expand=True,
            password=is_secret, can_reveal_password=is_secret,
            bgcolor=AppColors.SURFACE, border_color=ft.Colors.GREY_800,
            focused_border_color=AppColors.ACCENT,
            content_padding=ft.padding.symmetric(horizontal=12)
        )
        return ft.Row([
            text_field,
            ft.IconButton(
                ft.Icons.SAVE_ROUNDED, icon_color=ft.Colors.GREEN_400, icon_size=20,
                on_click=lambda _: self._save_individual(config_key, sub_key, text_field.value)
            )
        ], spacing=5)

    def _user_field(self, label, value, field_key, secret=False):
        text_field = ft.TextField(
            label=label, value=str(value), height=45, text_size=12, expand=True,
            password=secret, can_reveal_password=secret,
            bgcolor=AppColors.SURFACE, border_color=ft.Colors.GREY_800,
            focused_border_color=AppColors.ACCENT,
            content_padding=ft.padding.symmetric(horizontal=12)
        )
        return ft.Row([
            text_field,
            ft.IconButton(
                ft.Icons.SAVE_ROUNDED, icon_color=ft.Colors.GREEN_400, icon_size=20,
                on_click=lambda _, k=field_key, tf=text_field: (
                    db.save_user_config(username=self.username_actual, **{k: tf.value.strip()}),
                    self._show_snackbar("✅ Guardado correctamente", ft.Colors.GREEN_700)
                )
            )
        ], spacing=5)

    def build(self) -> ft.Tab:
        if self.user_tier < 3:
            user_config = db.get_user_config(self.username_actual) or {}

            col_1 = ft.Column([
                ft.Text("CONEXIÓN TWITCH", weight="bold", color=AppColors.ACCENT, size=14),
                self._user_field("Canal", user_config.get("channel", ""), "channel"),
                self._user_field("Nombre del Bot", user_config.get("bot_name", ""), "bot_name"),
                self._user_field("Broadcaster ID", user_config.get("broadcaster_id", ""), "broadcaster_id", secret=True),
                ft.Divider(height=30, color="transparent"),
                ft.Text("TOKENS DEL BOT", weight="bold", color=ft.Colors.PURPLE_400, size=14),
                self._user_field("Token del Bot", user_config.get("token_bot", ""), "token_bot", secret=True),
                self._user_field("Client ID del Bot", user_config.get("client_id_bot", ""), "client_id_bot", secret=True),
                ft.Divider(height=20, color="transparent"),
                ft.Text("ENLACES DE AYUDA", weight="bold", color=ft.Colors.GREY_500, size=12),
                ft.Row([
                    ft.TextButton("Obtener Tokens", icon=ft.Icons.LINK,
                                  on_click=lambda _: self.page.launch_url("https://twitchtokengenerator.com/")),
                    ft.TextButton("Mi ID", icon=ft.Icons.FINGERPRINT,
                                  on_click=lambda _: self.page.launch_url("https://www.streamweasels.com/tools/convert-twitch-username-to-user-id/")),
                    ft.TextButton("Dev Console", icon=ft.Icons.CODE,
                                  on_click=lambda _: self.page.launch_url("https://dev.twitch.tv/console")),
                ], wrap=True)
            ], expand=True, spacing=10)

            col_2 = ft.Column([
                ft.Text("ADMINISTRACIÓN", weight="bold", color=ft.Colors.BLUE_400, size=14),
                self._user_field("Moderadores (separados por coma)", user_config.get("mods", ""), "mods"),
                ft.Divider(height=20, color="transparent"),
                ft.Text("SEGURIDAD BROADCASTER", weight="bold", color=ft.Colors.RED_400, size=14),
                self._user_field("Token Broadcaster", user_config.get("token", ""), "token", secret=True),
                self._user_field("Client ID", user_config.get("client_id", ""), "client_id", secret=True),
                self._user_field("Client Secret", user_config.get("client_secret", ""), "client_secret", secret=True),
            ], expand=True, spacing=10)

            return ft.Tab(
                text="CONFIGURACIÓN", icon=ft.Icons.SETTINGS,
                content=ft.Container(
                    padding=30, bgcolor=AppColors.BG_DARK,
                    content=ft.Column([
                        ft.Row([
                            ft.Icon(ft.Icons.SETTINGS_SUGGEST, color=AppColors.ACCENT, size=30),
                            ft.Column([
                                ft.Text("MI CONFIGURACIÓN", size=20, weight="bold"),
                                ft.Text(f"Sesión: {self.username_actual}", size=12, color="gray"),
                            ], spacing=0)
                        ]),
                        ft.Divider(height=20, color=ft.Colors.WHITE10),
                        ft.Row(
                            [col_1, ft.VerticalDivider(width=40, color=ft.Colors.WHITE10), col_2],
                            expand=True, vertical_alignment=ft.CrossAxisAlignment.START
                        )
                    ], scroll=ft.ScrollMode.AUTO)
                )
            )

        # Admin
        col_1 = ft.Column([
            ft.Text("CONEXIÓN TWITCH", weight="bold", color=AppColors.ACCENT, size=14),
            self.create_setting_field("Canal (Streamer)", self.config["twitch"]["channel"], "twitch", "channel"),
            self.create_setting_field("Nombre del Bot", self.config["twitch"]["bot_name"], "twitch", "bot_name"),
            self.create_setting_field("Broadcaster ID", self.config["twitch"]["broadcaster_id"], "twitch", "broadcaster_id"),
            ft.Divider(height=30, color="transparent"),
            ft.Text("TOKENS DEL BOT", weight="bold", color=ft.Colors.PURPLE_400, size=14),
            self.create_setting_field("Token Bot", self.config["twitch"]["token_bot"], "twitch", "token_bot"),
            self.create_setting_field("Client ID Bot", self.config["twitch"]["client_id_bot"], "twitch", "client_id_bot"),
            ft.Divider(height=20, color="transparent"),
            ft.Text("ENLACES DE AYUDA", weight="bold", color=ft.Colors.GREY_500, size=12),
            ft.Row([
                ft.TextButton("Obtener Tokens", icon=ft.Icons.LINK,
                              on_click=lambda _: self.page.launch_url("https://twitchtokengenerator.com/")),
                ft.TextButton("Mi ID", icon=ft.Icons.FINGERPRINT,
                              on_click=lambda _: self.page.launch_url("https://www.streamweasels.com/tools/convert-twitch-username-to-user-id/")),
                ft.TextButton("Consola Developer", icon=ft.Icons.CODE,
                              on_click=lambda _: self.page.launch_url("https://dev.twitch.tv/console")),
            ], wrap=True)
        ], expand=True, spacing=10)

        col_2_controls = [
            ft.Text("INTELIGENCIA ARTIFICIAL (TIER 3)", weight="bold", color=ft.Colors.GREEN_400, size=14),
            self.create_setting_field("OpenAI API Key", self.config["openai"]["api_key"], "openai", "api_key"),
            ft.Divider(height=20, color="transparent"),
            ft.Text("ADMINISTRACIÓN", weight="bold", color=ft.Colors.BLUE_400, size=14),
            self.create_setting_field("Moderadores (separados por coma)", ", ".join(self.config["admin_users"]), "admin_users"),
            ft.Divider(height=20, color="transparent"),
            ft.Text("SEGURIDAD BROADCASTER", weight="bold", color=ft.Colors.RED_400, size=14),
            self.create_setting_field("Token Broadcaster", self.config["twitch"]["token"], "twitch", "token"),
            self.create_setting_field("Client ID", self.config["twitch"]["client_id"], "twitch", "client_id"),
            self.create_setting_field("Client Secret", self.config["twitch"]["client_secret"], "twitch", "client_secret"),
        ]

        col_2 = ft.Column(col_2_controls, expand=True, spacing=10)

        return ft.Tab(
            text="CONFIGURACIÓN", icon=ft.Icons.SETTINGS,
            content=ft.Container(
                padding=30, bgcolor=AppColors.BG_DARK,
                content=ft.Column([
                    ft.Row([
                        ft.Icon(ft.Icons.SETTINGS_SUGGEST, color=AppColors.ACCENT, size=30),
                        ft.Column([
                            ft.Text("PANEL TÉCNICO", size=20, weight="bold"),
                            ft.Text(f"Sesión: {self.username_actual}", size=12, color="gray"),
                        ], spacing=0)
                    ]),
                    ft.Divider(height=20, color=ft.Colors.WHITE10),
                    ft.Row(
                        [col_1, ft.VerticalDivider(width=40, color=ft.Colors.WHITE10), col_2],
                        expand=True, vertical_alignment=ft.CrossAxisAlignment.START
                    )
                ], scroll=ft.ScrollMode.AUTO)
            )
        )

    def _show_snackbar(self, text, color):
        self.page.snack_bar = ft.SnackBar(
            content=ft.Text(text, color="white"), bgcolor=color, duration=2000
        )
        self.page.snack_bar.open = True
        self.page.update()