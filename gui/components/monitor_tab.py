import flet as ft

def build_monitor_tab(terminal_list, chat_list, power_btn, clear_term_fn, clear_chat_fn):
    return ft.Tab(
        text="Monitor",
        icon=ft.Icons.TERMINAL,
        content=ft.Container(padding=20, content=ft.Column([
            ft.Row([
                ft.Column([
                    ft.Text("SISTEMA", weight="bold", size=12),
                    ft.Container(terminal_list, expand=True, bgcolor="#0d0d0d", padding=10, border_radius=10, border=ft.border.all(1, ft.Colors.GREY_900)),
                    ft.Row([ft.Container(expand=True), ft.IconButton(ft.Icons.DELETE_OUTLINE, on_click=clear_term_fn)])
                ], expand=1),
                ft.Column([
                    ft.Text("CHAT Y COMANDOS", weight="bold", size=12),
                    ft.Container(chat_list, expand=True, bgcolor="#0d0d0d", padding=10, border_radius=10, border=ft.border.all(1, ft.Colors.GREY_900)),
                    ft.Row([ft.Container(expand=True), ft.IconButton(ft.Icons.DELETE_OUTLINE, on_click=clear_chat_fn)])
                ], expand=1)
            ], expand=True, spacing=20),
            ft.Row([power_btn], alignment=ft.MainAxisAlignment.CENTER)
        ]))
    )