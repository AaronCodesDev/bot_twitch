import flet as ft
from gui.styles import AppColors

class DashboardHeader:
    # Solo 5 argumentos (sin btn_power)
    def __init__(self, username: str, tier: int, status_dot, status_text, on_logout):
        self.username = username
        self.tier = tier
        self.status_dot = status_dot
        self.status_text = status_text
        self.on_logout = on_logout
    
    def build(self):
        tier_label = self._get_tier_label()
        tier_color = self._get_tier_color()
        
        return ft.Container(
            padding=ft.padding.symmetric(horizontal=20, vertical=15),
            bgcolor=AppColors.SURFACE,
            border=ft.border.only(bottom=ft.BorderSide(1, ft.Colors.GREY_900)),
            content=ft.Row([
                ft.Row([
                    ft.Icon(ft.Icons.SPEED, color=AppColors.ACCENT, size=28),
                    ft.Column([
                        ft.Text(f"PANEL - {self.username.upper()}", size=18, weight="bold", color=ft.Colors.WHITE),
                        ft.Row([
                            ft.Text("RANGO:", size=10, color="white50"),
                            ft.Text(f"TIER {self.tier} {tier_label}", size=10, weight="bold", color=tier_color)
                        ], spacing=5)
                    ], spacing=0)
                ], spacing=10),

                ft.Row([
                    ft.Row([self.status_dot, self.status_text], spacing=8),
                    ft.VerticalDivider(width=20, color=ft.Colors.GREY_800),
                    ft.TextButton(
                        "LOGOUT",
                        icon=ft.Icons.LOGOUT,
                        on_click=lambda _: self.on_logout(),
                        style=ft.ButtonStyle(color="orange")
                    ),
                ])
            ], alignment=ft.MainAxisAlignment.SPACE_BETWEEN)
        )

    def _get_tier_label(self) -> str:
        if self.tier == 1: return "(Gratuito)"
        elif self.tier == 2: return "(Suscripción)"
        return "(Administrador)"
    
    def _get_tier_color(self):
        if self.tier == 3: return AppColors.T3_COLOR
        elif self.tier == 2: return AppColors.T2_COLOR
        return AppColors.T1_COLOR