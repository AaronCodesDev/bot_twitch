# gui/dialogs/setup_dialog.py
import flet as ft
from gui.styles import AppColors
from core.database import db


class SetupDialog:
    """Popup informativo de bienvenida"""

    def __init__(self, page: ft.Page, username: str, on_success=None):
        self.page = page
        self.username = username
        self.on_success = on_success

        self.dialog = ft.AlertDialog(
            modal=True,
            on_dismiss=lambda e: None,
            title=ft.Row([
                ft.Icon(ft.Icons.ROCKET_LAUNCH, color=AppColors.ACCENT),
                ft.Text(
                    f"¡Bienvenido, {username.upper()}!",
                    size=18, weight="bold", color=AppColors.ACCENT
                )
            ]),
            content=ft.Container(
                width=450,
                padding=10,
                content=ft.Column([
                    ft.Text(
                        "Para usar el bot necesitas configurar tu canal de Twitch.",
                        size=13, color="white"
                    ),
                    ft.Text(
                        "Necesitarás los siguientes datos:",
                        size=12, color="white60"
                    ),
                    ft.Container(
                        content=ft.Column([
                            ft.Row([ft.Icon(ft.Icons.TV, size=16, color=AppColors.ACCENT), ft.Text("Nombre de tu canal", size=12, color="white70")]),
                            ft.Row([ft.Icon(ft.Icons.SMART_TOY, size=16, color=AppColors.ACCENT), ft.Text("Nombre del bot", size=12, color="white70")]),
                            ft.Row([ft.Icon(ft.Icons.FINGERPRINT, size=16, color=AppColors.ACCENT), ft.Text("Broadcaster ID", size=12, color="white70")]),
                            ft.Row([ft.Icon(ft.Icons.KEY, size=16, color=AppColors.ACCENT), ft.Text("Token del Bot y Token Broadcaster", size=12, color="white70")]),
                            ft.Row([ft.Icon(ft.Icons.CODE, size=16, color=AppColors.ACCENT), ft.Text("Client ID y Client Secret", size=12, color="white70")]),
                            ft.Row([ft.Icon(ft.Icons.SHIELD, size=16, color=AppColors.ACCENT), ft.Text("Moderadores de tu canal", size=12, color="white70")]),
                        ], spacing=8),
                        bgcolor=AppColors.SURFACE,
                        border_radius=8,
                        padding=12,
                    ),
                    ft.Divider(color=ft.Colors.GREY_800),
                    ft.Text("ENLACES DE AYUDA", size=11, weight="bold", color="white40"),
                    ft.Row([
                        ft.TextButton("Tokens", icon=ft.Icons.LINK,
                            on_click=lambda _: self.page.launch_url("https://twitchtokengenerator.com/")),
                        ft.TextButton("Mi ID", icon=ft.Icons.FINGERPRINT,
                            on_click=lambda _: self.page.launch_url("https://www.streamweasels.com/tools/convert-twitch-username-to-user-id/")),
                        ft.TextButton("Dev Console", icon=ft.Icons.CODE,
                            on_click=lambda _: self.page.launch_url("https://dev.twitch.tv/console")),
                    ], wrap=True),
                ], spacing=12)
            ),
            actions=[
                ft.TextButton(
                    "Más tarde",
                    on_click=self._skip,
                    style=ft.ButtonStyle(color="white30")
                ),
                ft.ElevatedButton(
                    "EMPEZAR CONFIGURACIÓN",
                    icon=ft.Icons.ARROW_FORWARD,
                    bgcolor=AppColors.ACCENT,
                    color="white",
                    on_click=self._go_to_config
                )
            ],
            actions_alignment=ft.MainAxisAlignment.END
        )

    def open(self):
        if self.dialog not in self.page.overlay:
            self.page.overlay.append(self.dialog)
        self.dialog.open = True
        self.page.update()

    def _skip(self, e):
        self.dialog.open = False
        self.page.update()

    def _go_to_config(self, e):
        self.dialog.open = False
        self.page.update()
        SetupFormDialog(self.page, self.username, self.on_success).open()


class SetupFormDialog:
    """Dialog grande de configuración"""

    def __init__(self, page: ft.Page, username: str, on_success=None):
        self.page = page
        self.username = username
        self.on_success = on_success

        config = db.get_user_config(username) or {}

        self.channel_field = ft.TextField(
            label="Tu canal de Twitch", hint_text="Ej: mi_canal",
            value=config.get("channel", ""),
            bgcolor=AppColors.SURFACE, color="white",
            border_color=ft.Colors.GREY_700, focused_border_color=AppColors.ACCENT,
            expand=True
        )
        self.bot_name_field = ft.TextField(
            label="Nombre del Bot", hint_text="Ej: mi_bot",
            value=config.get("bot_name", ""),
            bgcolor=AppColors.SURFACE, color="white",
            border_color=ft.Colors.GREY_700, focused_border_color=AppColors.ACCENT,
            expand=True
        )
        self.broadcaster_id_field = ft.TextField(
            label="Broadcaster ID", hint_text="Tu ID numérico de Twitch",
            value=config.get("broadcaster_id", ""),
            bgcolor=AppColors.SURFACE, color="white",
            border_color=ft.Colors.GREY_700, focused_border_color=AppColors.ACCENT,
            expand=True
        )
        self.token_bot_field = ft.TextField(
            label="Token del Bot", hint_text="oauth:xxxxxxxx",
            value=config.get("token_bot", ""),
            password=True, can_reveal_password=True,
            bgcolor=AppColors.SURFACE, color="white",
            border_color=ft.Colors.GREY_700, focused_border_color=AppColors.ACCENT,
            expand=True
        )
        self.client_id_bot_field = ft.TextField(
            label="Client ID del Bot",
            value=config.get("client_id_bot", ""),
            password=True, can_reveal_password=True,
            bgcolor=AppColors.SURFACE, color="white",
            border_color=ft.Colors.GREY_700, focused_border_color=AppColors.ACCENT,
            expand=True
        )
        self.token_field = ft.TextField(
            label="Token Broadcaster", hint_text="oauth:xxxxxxxx",
            value=config.get("token", ""),
            password=True, can_reveal_password=True,
            bgcolor=AppColors.SURFACE, color="white",
            border_color=ft.Colors.GREY_700, focused_border_color=AppColors.ACCENT,
            expand=True
        )
        self.client_id_field = ft.TextField(
            label="Client ID Broadcaster",
            value=config.get("client_id", ""),
            password=True, can_reveal_password=True,
            bgcolor=AppColors.SURFACE, color="white",
            border_color=ft.Colors.GREY_700, focused_border_color=AppColors.ACCENT,
            expand=True
        )
        self.client_secret_field = ft.TextField(
            label="Client Secret",
            value=config.get("client_secret", ""),
            password=True, can_reveal_password=True,
            bgcolor=AppColors.SURFACE, color="white",
            border_color=ft.Colors.GREY_700, focused_border_color=AppColors.ACCENT,
            expand=True
        )
        self.mods_field = ft.TextField(
            label="Moderadores", hint_text="mod1, mod2, mod3",
            value=config.get("mods", ""),
            bgcolor=AppColors.SURFACE, color="white",
            border_color=ft.Colors.GREY_700, focused_border_color=AppColors.ACCENT,
            prefix_icon=ft.Icons.SHIELD, expand=True
        )

        self.dialog = ft.AlertDialog(
            modal=True,
            on_dismiss=lambda e: None,
            title=ft.Row([
                ft.Icon(ft.Icons.SETTINGS, color=AppColors.ACCENT),
                ft.Text(
                    f"Configuración de {username.upper()}",
                    size=16, weight="bold", color=AppColors.ACCENT
                )
            ]),
            content=ft.Container(
                width=900,
                height=500,
                padding=10,
                content=ft.Row([
                    ft.Column([
                        ft.Text("CONEXIÓN", size=11, weight="bold", color="white40"),
                        self.channel_field,
                        self.bot_name_field,
                        self.broadcaster_id_field,
                        ft.Divider(color=ft.Colors.GREY_800),
                        ft.Text("TOKENS DEL BOT", size=11, weight="bold", color="white40"),
                        self.token_bot_field,
                        self.client_id_bot_field,
                    ], spacing=10, expand=True),
                    ft.VerticalDivider(width=30, color=ft.Colors.GREY_800),
                    ft.Column([
                        ft.Text("SEGURIDAD BROADCASTER", size=11, weight="bold", color="white40"),
                        self.token_field,
                        self.client_id_field,
                        self.client_secret_field,
                        ft.Divider(color=ft.Colors.GREY_800),
                        ft.Text("MODERADORES", size=11, weight="bold", color="white40"),
                        self.mods_field,
                        ft.Text(
                            "Separa con comas. Ej: mod1, mod2",
                            size=10, color="white30", italic=True
                        ),
                    ], spacing=10, expand=True),
                ], expand=True, vertical_alignment=ft.CrossAxisAlignment.START)
            ),
            actions=[
                ft.TextButton(
                    "Cancelar",
                    on_click=self._close,
                    style=ft.ButtonStyle(color="white30")
                ),
                ft.ElevatedButton(
                    "GUARDAR",
                    icon=ft.Icons.SAVE,
                    bgcolor=AppColors.ACCENT,
                    color="white",
                    on_click=self._save
                )
            ],
            actions_alignment=ft.MainAxisAlignment.END
        )

    def open(self):
        if self.dialog not in self.page.overlay:
            self.page.overlay.append(self.dialog)
        self.dialog.open = True
        self.page.update()

    def _close(self, e):
        self.dialog.open = False
        self.page.update()

    def _save(self, e):
        db.save_user_config(
            username=self.username,
            channel=self.channel_field.value.strip(),
            bot_name=self.bot_name_field.value.strip(),
            broadcaster_id=self.broadcaster_id_field.value.strip(),
            token_bot=self.token_bot_field.value.strip(),
            client_id_bot=self.client_id_bot_field.value.strip(),
            token=self.token_field.value.strip(),
            client_id=self.client_id_field.value.strip(),
            client_secret=self.client_secret_field.value.strip(),
            mods=self.mods_field.value.strip(),
            setup_done=1
        )
        self._close(e)
        self.page.snack_bar = ft.SnackBar(
            content=ft.Text("✅ Configuración guardada correctamente"),
            bgcolor=ft.Colors.GREEN_700, duration=3000
        )
        self.page.snack_bar.open = True
        self.page.update()
        if self.on_success and callable(self.on_success):
            self.on_success()