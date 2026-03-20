import flet as ft
from gui.styles import AppColors

def build_phrases_tab(file_list_column, var_dropdown, phrase_editor, save_fn):
    return ft.Tab(
        text="Frases",
        icon=ft.Icons.EDIT_NOTE,
        content=ft.Row([
            # Sidebar
            ft.Container(
                width=230,
                bgcolor=AppColors.SURFACE,
                padding=15,
                content=ft.Column([
                    ft.Text("ARCHIVOS PY", weight="bold", size=12),
                    ft.Divider(color="#333333"),
                    file_list_column
                ], scroll=ft.ScrollMode.AUTO)
            ),
            # Editor
            ft.Container(
                expand=True,
                padding=25,
                content=ft.Column([
                    ft.Row([
                        var_dropdown,
                        ft.ElevatedButton(
                            "GUARDAR", 
                            icon=ft.Icons.SAVE,
                            on_click=save_fn,
                            bgcolor=ft.Colors.GREEN_700,
                            color="white"
                        )
                    ]),
                    phrase_editor
                ])
            )
        ], spacing=0)
    )