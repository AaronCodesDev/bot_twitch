# gui/auth/login_screen.py
import flet as ft
import json
import os
from gui.auth.auth_service import AuthService
from gui.dialogs.user_dialog import RegisterDialog

REMEMBER_FILE = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))), "data", "remember.json")

def load_remembered():
    try:
        if os.path.exists(REMEMBER_FILE):
            with open(REMEMBER_FILE, "r") as f:
                return json.load(f).get("username", "")
    except:
        pass
    return ""

def save_remembered(username: str):
    try:
        os.makedirs(os.path.dirname(REMEMBER_FILE), exist_ok=True)
        with open(REMEMBER_FILE, "w") as f:
            json.dump({"username": username}, f)
    except:
        pass

def clear_remembered():
    try:
        if os.path.exists(REMEMBER_FILE):
            os.remove(REMEMBER_FILE)
    except:
        pass

class LoginScreen:
    def __init__(self, page: ft.Page, on_success):
        self.page = page
        self.on_success = on_success
        self.auth_service = AuthService()
        self.page.padding = 0

    def _handle_login(self, u_field, p_field, remember_cb):
        username = u_field.value
        password = p_field.value
        if not username or not password:
            return

        result = self.auth_service.login(username, password)
        if result:
            user, tier = result
            try:
                tier_int = int(tier)
            except:
                tier_int = 1

            # Remember me
            if remember_cb.value:
                save_remembered(username)
            else:
                clear_remembered()

            self.page.session.set("username", username)
            self.page.session.set("user_tier", tier_int)
            print(f"✅ Login exitoso: {username} (Tier {tier_int}) guardado en sesión.")
            self.on_success(user, tier_int)
        else:
            self.page.snack_bar = ft.SnackBar(
                content=ft.Text("Usuario o contraseña incorrectos", color="white"),
                bgcolor=ft.Colors.RED_700,
                duration=3000
            )
            self.page.snack_bar.open = True
            self.page.update()

    def show(self):
        remembered = load_remembered()

        username_field = ft.TextField(
            label="Username", value=remembered, width=280, height=45, border_radius=10,
            bgcolor="black26", border_color="white24", color="white",
            prefix_icon=ft.Icons.PERSON_OUTLINE
        )
        password_field = ft.TextField(
            label="Password", width=280, height=45, border_radius=10,
            bgcolor="black26", border_color="white24", password=True,
            can_reveal_password=True, color="white", prefix_icon=ft.Icons.LOCK_OUTLINE
        )
        remember_cb = ft.Checkbox(
            label="Remember me",
            value=bool(remembered),
            label_style=ft.TextStyle(size=11, color="white70")
        )

        login_card = ft.Container(
            width=360,
            height=520,
            padding=40,
            border_radius=30,
            bgcolor=ft.Colors.with_opacity(0.1, "white"),
            border=ft.border.all(1, "white10"),
            blur=ft.Blur(25, 25),
            content=ft.Column(
                [
                    ft.Text("Login", size=32, weight="bold", color="white"),
                    ft.Container(height=10),
                    username_field,
                    password_field,
                    ft.Row([
                        remember_cb,
                        ft.TextButton(
                            "Forgot?",
                            style=ft.ButtonStyle(color="white30"),
                            on_click=lambda _: self._show_forgot()
                        )
                    ], alignment="spaceBetween", width=280),
                    ft.Container(height=15),
                    ft.ElevatedButton(
                        "LOGIN", width=280, height=48, bgcolor="white", color="black",
                        on_click=lambda _: self._handle_login(username_field, password_field, remember_cb),
                        style=ft.ButtonStyle(shape=ft.RoundedRectangleBorder(radius=12))
                    ),
                    ft.Row([
                        ft.Text("New here?", size=12, color="white60"),
                        ft.TextButton(
                            "Register",
                            on_click=lambda _: RegisterDialog(self.page, None).open(),
                            style=ft.ButtonStyle(color="white")
                        )
                    ], alignment="center"),
                ],
                horizontal_alignment="center",
                alignment="center",
                spacing=12
            )
        )

        bg_image = ft.Container(
            expand=True,
            image=ft.DecorationImage(
                src="background.jpg",
                fit=ft.ImageFit.COVER,
            )
        )

        self.page.clean()
        self.page.add(
            ft.Stack(
                [
                    bg_image,
                    ft.Container(expand=True, bgcolor=ft.Colors.with_opacity(0.3, "black")),
                    ft.Container(
                        content=login_card,
                        alignment=ft.alignment.center,
                        expand=True,
                    )
                ],
                expand=True
            )
        )
        self.page.update()

    def _show_forgot(self):
        dialog = ft.AlertDialog(
            title=ft.Text("¿Olvidaste tu contraseña?", weight="bold"),
            content=ft.Text(
                "Contacta con el administrador para resetear tu contraseña.\n\n"
                "El admin puede hacerlo desde el panel de ADMIN → editar usuario.",
                size=13, color="white70"
            ),
            actions=[
                ft.TextButton("Entendido", on_click=lambda e: self.page.close(dialog))
            ]
        )
        self.page.open(dialog)
        self.page.update()
