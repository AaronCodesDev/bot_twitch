import flet as ft
from gui.styles import AppColors, AppStyles

def build_subs_tab(subs_view_column, sync_fn, refresh_fn):
    return ft.Tab(
        text="Subs",
        icon=ft.Icons.STAR,
        content=ft.Container(
            padding=20,
            content=ft.Column([
                ft.Row([
                    ft.Text("SUSCRIPTORES ACTIVOS", weight="bold", size=16),
                    ft.Row([
                        ft.ElevatedButton("SINCRONIZAR", icon=ft.Icons.SYNC, on_click=sync_fn, bgcolor=ft.Colors.PURPLE_700),
                        ft.IconButton(ft.Icons.REFRESH, on_click=refresh_fn)
                    ])
                ], alignment=ft.MainAxisAlignment.SPACE_BETWEEN),
                ft.Divider(color="transparent", height=10),
                subs_view_column # Aquí se inyectan las tarjetas creadas en el main
            ])
        )
    )