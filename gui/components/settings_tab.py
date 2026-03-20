import flet as ft
from gui.styles import AppColors

def build_settings_tab(config_data, save_indiv_fn):
    
    # --- FUNCIÓN AUXILIAR PARA CREAR CAMPOS (IGUAL AL ORIGINAL) ---
    def create_setting_field(label, value, config_key, sub_key=None):
        # Detectamos si es un campo sensible para poner asteriscos
        is_secret = any(x in label.lower() for x in ["key", "token", "secret", "id"])
        
        text_field = ft.TextField(
            label=label, 
            value=str(value), 
            height=45, 
            text_size=12, 
            expand=True, 
            password=is_secret, 
            can_reveal_password=is_secret,
            border_color=ft.Colors.GREY_800,
            focused_border_color=ft.Colors.BLUE_400
        )
        
        # Botón de guardado individual que llama a la función del main
        save_btn = ft.IconButton(
            ft.Icons.SAVE, 
            on_click=lambda _: save_indiv_fn(config_key, sub_key, text_field.value), 
            icon_color=ft.Colors.GREEN_400,
            tooltip=f"Guardar {label}"
        )
        
        return ft.Row([text_field, save_btn], spacing=5)

    # --- COLUMNA 1: TWITCH ---
    ajustes_col_1 = ft.Column([
        ft.Text("CONEXIÓN TWITCH", weight="bold", color=ft.Colors.BLUE_400, size=14),
        create_setting_field("Canal", config_data["twitch"]["channel"], "twitch", "channel"),
        create_setting_field("Nombre Bot", config_data["twitch"]["bot_name"], "twitch", "bot_name"),
        create_setting_field("Broadcaster ID", config_data["twitch"]["broadcaster_id"], "twitch", "broadcaster_id"),
        
        ft.Container(height=10), # Espaciador
        
        ft.Text("TOKENS BOT", weight="bold", color=ft.Colors.PURPLE_400, size=14),
        create_setting_field("Token Bot", config_data["twitch"]["token_bot"], "twitch", "token_bot"),
        create_setting_field("Client ID Bot", config_data["twitch"]["client_id_bot"], "twitch", "client_id_bot")
    ], expand=1, spacing=15)

    # --- COLUMNA 2: IA & ADMIN ---
    ajustes_col_2 = ft.Column([
        ft.Text("IA & ADMIN", weight="bold", color=ft.Colors.GREEN_400, size=14),
        create_setting_field("OpenAI API Key", config_data["openai"]["api_key"], "openai", "api_key"),
        create_setting_field("Admins (separados por coma)", ", ".join(config_data["admin_users"]), "admin_users"),
        
        ft.Container(height=10), # Espaciador
        
        ft.Text("SEGURIDAD BROADCASTER", weight="bold", color=ft.Colors.RED_400, size=14),
        create_setting_field("Token Broadcaster", config_data["twitch"]["token"], "twitch", "token"),
        create_setting_field("Client ID Broadcaster", config_data["twitch"]["client_id"], "twitch", "client_id"),
        create_setting_field("Client Secret", config_data["twitch"]["client_secret"], "twitch", "client_secret")
    ], expand=1, spacing=15)

    # --- RETORNO DEL TAB ---
    return ft.Tab(
        text="Ajustes",
        icon=ft.Icons.SETTINGS,
        content=ft.Container(
            padding=30, 
            content=ft.Column([
                ft.Row([
                    ajustes_col_1, 
                    ft.VerticalDivider(width=40, color="#333333"), 
                    ajustes_col_2
                ], expand=True, vertical_alignment=ft.CrossAxisAlignment.START)
            ], scroll=ft.ScrollMode.AUTO)
        )
    )