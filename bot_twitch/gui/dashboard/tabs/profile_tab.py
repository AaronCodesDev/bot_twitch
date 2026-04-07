# gui/dashboard/tabs/profile_tab.py
import flet as ft
import os
import shutil
from gui.dashboard.tabs.base_tab import BaseTab
from gui.styles import AppColors
from gui.services.user_service import UserService
from gui.dialogs.profile_dialog import EditProfileDialog

BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
AVATARS_DIR = os.path.join(BASE_DIR, "gui", "assets", "avatars")

def get_avatar_path(username: str) -> str:
    for ext in ["jpg", "jpeg", "png", "webp"]:
        path = os.path.join(AVATARS_DIR, f"{username.lower()}.{ext}")
        if os.path.exists(path):
            return path
    return None

class ProfileTab(BaseTab):

    def __init__(self, page: ft.Page, username: str, tier: int):
        super().__init__(page)
        self.username = username
        self.tier = tier
        self.user_service = UserService()
        self.name_text = ft.Text("", size=14, color=ft.Colors.WHITE)
        self.email_text = ft.Text("", size=14, color=ft.Colors.WHITE)
        self.ref_code_text = ft.Text("", size=14, color="white30")
        self.tier_text = ft.Text("", size=14, weight="bold")
        self.avatar_container = ft.Container(width=100, height=100)
        self.file_picker = ft.FilePicker(on_result=self._on_avatar_picked)
        self.page.overlay.append(self.file_picker)

    def _get_tier_style(self):
        if self.tier == 3:
            return AppColors.T3_COLOR, AppColors.T3_BG, "ADMIN"
        elif self.tier == 2:
            return AppColors.T2_COLOR, AppColors.T2_BG, "SUSCRIPCIÓN"
        return AppColors.T1_COLOR, AppColors.T1_BG, "GRATUITO"

    def _build_avatar(self, tier_color):
        avatar_path = get_avatar_path(self.username)
        os.makedirs(AVATARS_DIR, exist_ok=True)

        if avatar_path:
            avatar_src = os.path.relpath(avatar_path, BASE_DIR).replace("\\", "/")
            avatar_widget = ft.Image(
                src=avatar_src,
                width=100, height=100,
                fit=ft.ImageFit.COVER,
                border_radius=50,
            )
        else:
            avatar_widget = ft.Icon(ft.Icons.ACCOUNT_CIRCLE, size=100, color=tier_color)

        self.avatar_container.content = ft.Stack([
            ft.Container(
                content=avatar_widget,
                width=100, height=100,
                border_radius=50,
                clip_behavior=ft.ClipBehavior.HARD_EDGE,
            ),
            ft.Container(
                content=ft.IconButton(
                    icon=ft.Icons.CAMERA_ALT,
                    icon_color="white",
                    icon_size=18,
                    on_click=lambda _: self.file_picker.pick_files(
                        allowed_extensions=["jpg", "jpeg", "png", "webp"],
                        allow_multiple=False
                    ),
                    style=ft.ButtonStyle(
                        bgcolor=ft.Colors.with_opacity(0.6, "black"),
                        padding=5
                    )
                ),
                bottom=0, right=0,
                border_radius=20,
            )
        ])
        return self.avatar_container

    def _on_avatar_picked(self, e: ft.FilePickerResultEvent):
        if not e.files:
            return
        file = e.files[0]
        ext = file.name.split(".")[-1].lower()
        dest = os.path.join(AVATARS_DIR, f"{self.username.lower()}.{ext}")
        os.makedirs(AVATARS_DIR, exist_ok=True)

        for old_ext in ["jpg", "jpeg", "png", "webp"]:
            old = os.path.join(AVATARS_DIR, f"{self.username.lower()}.{old_ext}")
            if os.path.exists(old) and old != dest:
                os.remove(old)

        shutil.copy2(file.path, dest)
        self._show_snackbar("Avatar actualizado correctamente", "green")
        self._refresh_avatar()

    def _refresh_avatar(self):
        tier_color, _, _ = self._get_tier_style()
        self._build_avatar(tier_color)
        self.page.update()

    def build(self) -> ft.Tab:
        self._load_profile()
        tier_color, tier_bg, tier_label = self._get_tier_style()
        self.tier_text.value = tier_label
        self.tier_text.color = tier_color

        return ft.Tab(
            text="PERFIL",
            icon=ft.Icons.PERSON,
            content=ft.Container(
                padding=20,
                bgcolor=AppColors.BG_DARK,
                content=ft.Column([
                    # Avatar centrado
                    ft.Container(
                        content=self._build_avatar(tier_color),
                        alignment=ft.alignment.center,
                        margin=ft.margin.only(bottom=20)
                    ),
                    # Tarjeta centrada con ancho fijo
                    ft.Container(
                        content=ft.Container(
                            content=ft.Column([
                                self._build_info_row("USUARIO", self.username.upper()),
                                ft.Divider(color=ft.Colors.GREY_900),
                                self._build_info_row("NOMBRE COMPLETO", self.name_text),
                                ft.Divider(color=ft.Colors.GREY_900),
                                self._build_info_row("EMAIL", self.email_text),
                                ft.Divider(color=ft.Colors.GREY_900),
                                ft.Row([
                                    ft.Text("CÓDIGO DE REFERIDO", size=12, color="white60", width=150),
                                    ft.Container(
                                        content=ft.Text(
                                            self.ref_code_text.value,
                                            size=13,
                                            color="white30",
                                            italic=True,
                                        ),
                                        bgcolor=ft.Colors.with_opacity(0.05, "white"),
                                        border_radius=6,
                                        padding=ft.padding.symmetric(horizontal=10, vertical=4),
                                        border=ft.border.all(1, "white10"),
                                    )
                                ]),
                                ft.Divider(color=ft.Colors.GREY_900),
                                self._build_info_row("ROL", self.tier_text),
                            ], spacing=10),
                            bgcolor=AppColors.SURFACE,
                            border_radius=10,
                            padding=20,
                            width=500,
                        ),
                        alignment=ft.alignment.center,
                    ),
                    # Botón centrado
                    ft.Container(
                        content=ft.ElevatedButton(
                            text="EDITAR PERFIL",
                            icon=ft.Icons.EDIT,
                            on_click=self._open_edit_dialog,
                            style=ft.ButtonStyle(
                                bgcolor=AppColors.ACCENT,
                                color="white",
                                padding=15
                            )
                        ),
                        alignment=ft.alignment.center,
                        margin=ft.margin.only(top=30)
                    )
                ], spacing=20, expand=True, horizontal_alignment=ft.CrossAxisAlignment.CENTER)
            )
        )

    def _build_info_row(self, label: str, value) -> ft.Row:
        return ft.Row([
            ft.Text(label, size=12, color="white60", width=150),
            ft.Text(
                value if isinstance(value, str) else value.value,
                size=14, color="white", weight="bold", expand=True
            )
        ], width=460)

    def _load_profile(self):
        profile = self.user_service.get_profile(self.username)
        if profile and isinstance(profile, dict):
            self.name_text.value = profile.get("full_name", "") or "No especificado"
            self.email_text.value = profile.get("email", "") or "No especificado"
            self.ref_code_text.value = profile.get("ref_code", "") or "No especificado"
        else:
            self.name_text.value = "No especificado"
            self.email_text.value = "No especificado"
            self.ref_code_text.value = "No especificado"
        self.page.update()

    def _open_edit_dialog(self, e):
        profile = self.user_service.get_profile(self.username)
        if profile and isinstance(profile, dict):
            dialog = EditProfileDialog(
                self.page,
                self.username,
                profile.get("full_name", ""),
                profile.get("email", ""),
                profile.get("ref_code", ""),
                self._on_profile_updated
            )
            dialog.open()
        else:
            self._show_snackbar("Error al cargar perfil", "red")

    def _on_profile_updated(self):
        self._load_profile()
        self._show_snackbar("Perfil actualizado correctamente", "green")

    def _show_snackbar(self, message: str, color: str):
        self.page.snack_bar = ft.SnackBar(
            content=ft.Text(message),
            bgcolor=color,
            duration=3000,
        )
        self.page.snack_bar.open = True
        self.page.update()