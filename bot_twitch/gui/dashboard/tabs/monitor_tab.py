import flet as ft
from gui.styles import AppColors, AppStyles

def build_monitor_tab(terminal_messages, chat_messages, clear_terminal_msg, clear_chat_msg):
    """
    Construye la pestaña de monitor con terminal y chat.
    Corregido error de 'multiple values for keyword argument expand'.
    """
    return ft.Tab(
        text="MONITOR",
        icon=ft.Icons.MONITOR_HEART,
        content=ft.Container(
            padding=20,
            bgcolor=AppColors.BG_DARK,
            content=ft.Column(
                [
                    ft.Row(
                        [
                            # Panel izquierdo: Sistema
                            ft.Container(
                                expand=1,
                                content=ft.Column(
                                    [
                                        ft.Row(
                                            [
                                                ft.Text("SISTEMA", size=14, weight="bold", color=AppColors.ACCENT),
                                                ft.IconButton(
                                                    icon=ft.Icons.DELETE_OUTLINE,
                                                    icon_size=18,
                                                    icon_color=ft.Colors.RED_400,
                                                    on_click=clear_terminal_msg,
                                                )
                                            ],
                                            alignment=ft.MainAxisAlignment.SPACE_BETWEEN
                                        ),
                                        ft.Container(
                                            content=terminal_messages,
                                            # Quitamos 'expand=True' de aquí porque ya viene en BOX_CONTAINER
                                            **AppStyles.BOX_CONTAINER 
                                        )
                                    ],
                                    spacing=10,
                                    expand=True
                                )
                            ),
                            
                            # Panel derecho: Chat
                            ft.Container(
                                expand=1,
                                content=ft.Column(
                                    [
                                        ft.Row(
                                            [
                                                ft.Text("CHAT", size=14, weight="bold", color=AppColors.ACCENT),
                                                ft.IconButton(
                                                    icon=ft.Icons.DELETE_OUTLINE,
                                                    icon_size=18,
                                                    icon_color=ft.Colors.RED_400,
                                                    on_click=clear_chat_msg,
                                                )
                                            ],
                                            alignment=ft.MainAxisAlignment.SPACE_BETWEEN
                                        ),
                                        ft.Container(
                                            content=chat_messages,
                                            # Quitamos 'expand=True' de aquí también
                                            **AppStyles.BOX_CONTAINER
                                        )
                                    ],
                                    spacing=10,
                                    expand=True
                                )
                            )
                        ],
                        spacing=20,
                        expand=True
                    ),
                ],
                expand=True
            )
        )
    )