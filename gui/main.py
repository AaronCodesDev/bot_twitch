import flet as ft
import json
import os
import datetime
import subprocess
import threading
import sys
import re

# --- CONFIGURACIÓN DE RUTAS ---
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CONFIG_PATH = os.path.join(BASE_DIR, 'config.json')
BOT_SCRIPT = os.path.join(BASE_DIR, 'app.py') 

def load_config():
    if os.path.exists(CONFIG_PATH):
        try:
            with open(CONFIG_PATH, 'r', encoding='utf-8') as f:
                return json.load(f)
        except: pass
    return {"openai": {"api_key": ""}, "twitch": {"channel": "fantan", "token": "", "bot_name": ""}}

def get_phrases_from_file(category):
    # Ahora la ruta es fija a hello.py
    path = os.path.join(BASE_DIR, 'phrases', 'hello.py')
    if os.path.exists(path):
        try:
            with open(path, 'r', encoding='utf-8') as f:
                content = f.read()
                
                # Buscamos la variable específica (ej: hello_subs = [ ... ])
                # Usamos una expresión regular que busque el nombre de la categoría
                pattern = rf"{category}\s*=\s*\[(.*?)\]"
                match = re.search(pattern, content, re.DOTALL)
                
                if match:
                    raw_list_content = match.group(1)
                    phrases = []
                    # Limpiamos comillas y espacios
                    for p in raw_list_content.split(','):
                        clean_p = p.strip().strip('"').strip("'")
                        if clean_p:
                            phrases.append(clean_p)
                    return "\n".join(phrases)
                else:
                    return f"No se encontró la lista '{category}' dentro de hello.py"
        except Exception as e:
            return f"Error al leer hello.py: {str(e)}"
    return f"No se encontró el archivo: {path}"

def save_phrases_to_file(category, text_content):
    path = os.path.join(BASE_DIR, 'phrases', 'hello.py')
    if not os.path.exists(path):
        return
    
    # Preparamos el nuevo bloque de la lista
    phrases = text_content.split('\n')
    formatted_phrases = ",\n".join([f'    "{p.strip().replace("\"", "\\\"")}"' for p in phrases if p.strip()])
    new_list_block = f"{category} = [\n{formatted_phrases}\n]"
    
    try:
        with open(path, 'r', encoding='utf-8') as f:
            full_content = f.read()
        
        # Reemplazamos la lista vieja por la nueva usando regex
        pattern = rf"{category}\s*=\s*\[.*?\]"
        updated_content = re.sub(pattern, new_list_block, full_content, flags=re.DOTALL)
        
        with open(path, 'w', encoding='utf-8') as f:
            f.write(updated_content)
    except Exception as e:
        print(f"Error al guardar: {e}")

def main(page: ft.Page):
    page.title = "FANTAN BOT - Panel"
    page.theme_mode = ft.ThemeMode.DARK
    # Nueva sintaxis para el tamaño de ventana
    page.window.width = 900
    page.window.height = 900
    
    page.bot_process = None
    config_data = load_config()

    # --- COMPONENTES MONITOR ---
    status_dot = ft.CircleAvatar(bgcolor=ft.Colors.RED, radius=8)
    status_text = ft.Text("DESCONECTADO", color=ft.Colors.RED_400, weight="bold")
    terminal_messages = ft.Column(scroll=ft.ScrollMode.ALWAYS)
    terminal_container = ft.Container(
        content=terminal_messages, bgcolor=ft.Colors.BLACK, border_radius=10,
        padding=15, height=450, border=ft.border.all(1, ft.Colors.GREY_800)
    )

    def add_log(message, color=ft.Colors.WHITE):
        now = datetime.datetime.now().strftime("%H:%M:%S")
        if message.strip():
            terminal_messages.controls.append(ft.Text(f"[{now}] {message.strip()}", color=color, font_family="monospace", size=12))
            page.update()

    # --- COMPONENTES EDITOR ---
    phrase_editor = ft.TextField(
        label="Editar frases (una por línea)",
        multiline=True, min_lines=15, max_lines=20, text_size=13
    )
    
    category_dropdown = ft.Dropdown(
        label="Seleccionar Categoría",
        width=300,
        options=[
            ft.dropdown.Option("hello_subs", "Subscriptores"),
            ft.dropdown.Option("hello_favorites", "Favoritos"),
            ft.dropdown.Option("hello_normal", "Normales"),
            ft.dropdown.Option("hello_unfriendly", "Bordes/Tóxicos"),
        ],
        on_change=lambda e: update_editor_content()
    )

    def update_editor_content():
        if category_dropdown.value:
            content = get_phrases_from_file(category_dropdown.value)
            phrase_editor.value = content
            page.update()

    # --- AJUSTES ---
    api_key_input = ft.TextField(label="OpenAI API Key", value=config_data['openai'].get('api_key', ''), password=True, can_reveal_password=True)
    twitch_token = ft.TextField(label="Twitch Token", value=config_data['twitch'].get('token', ''), password=True, expand=True)
    twitch_channel = ft.TextField(label="Canal", value=config_data['twitch'].get('channel', ''), expand=True)

    def toggle_bot(e):
        if page.bot_process is None:
            config_data['openai']['api_key'] = api_key_input.value
            config_data['twitch']['token'] = twitch_token.value
            config_data['twitch']['channel'] = twitch_channel.value
            save_config_json(config_data)
            try:
                env_vars = os.environ.copy()
                env_vars["PYTHONIOENCODING"] = "utf-8"
                page.bot_process = subprocess.Popen(
                    [sys.executable, BOT_SCRIPT], stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
                    text=True, bufsize=1, universal_newlines=True, cwd=BASE_DIR, env=env_vars
                )
                def read_output():
                    for line in iter(page.bot_process.stdout.readline, ""):
                        add_log(line)
                threading.Thread(target=read_output, daemon=True).start()
                status_dot.bgcolor, status_text.value = ft.Colors.GREEN, "CONECTADO"
                btn_power.text, btn_power.bgcolor = "DETENER BOT", ft.Colors.RED_700
            except Exception as ex: add_log(f"❌ ERROR: {ex}", ft.Colors.RED)
        else:
            page.bot_process.terminate()
            page.bot_process = None
            status_dot.bgcolor, status_text.value = ft.Colors.RED, "DESCONECTADO"
            btn_power.text, btn_power.bgcolor = "ENCENDER BOT", ft.Colors.BLUE_700
        page.update()

    btn_power = ft.ElevatedButton("ENCENDER BOT", icon=ft.Icons.POWER_SETTINGS_NEW, on_click=toggle_bot, bgcolor=ft.Colors.BLUE_700, color="white", height=50)

    # --- TABS (CORREGIDOS SIN PADDING EN COLUMN) ---
    tabs = ft.Tabs(
        selected_index=0,
        tabs=[
            ft.Tab(
                text="Monitor", icon=ft.Icons.TERMINAL,
                content=ft.Container(
                    padding=20,
                    content=ft.Column([
                        ft.Row([status_dot, status_text]),
                        terminal_container,
                        ft.Row([btn_power], alignment=ft.MainAxisAlignment.CENTER)
                    ], spacing=20)
                )
            ),
            ft.Tab(
                text="Editor de Frases", icon=ft.Icons.EDIT_NOTE,
                content=ft.Container(
                    padding=20,
                    content=ft.Column([
                        ft.Text("Gestionar Respuestas del Bot", size=20, weight="bold"),
                        ft.Row([category_dropdown, ft.ElevatedButton("Cargar", on_click=lambda _: update_editor_content())]),
                        phrase_editor,
                        ft.ElevatedButton("GUARDAR CATEGORÍA", icon=ft.Icons.SAVE, on_click=lambda _: save_phrases_to_file(category_dropdown.value, phrase_editor.value), bgcolor=ft.Colors.GREEN_700, color="white")
                    ], spacing=20)
                )
            ),
            ft.Tab(
                text="Ajustes", icon=ft.Icons.SETTINGS,
                content=ft.Container(
                    padding=20,
                    content=ft.Column([
                        api_key_input,
                        ft.Row([twitch_token, twitch_channel]),
                        ft.ElevatedButton("Guardar Configuración", on_click=lambda _: save_config_json(config_data))
                    ], spacing=20)
                )
            )
        ],
        expand=1
    )

    page.add(ft.Text("🏎️ FANTAN PANEL", size=30, weight="bold"), tabs)

if __name__ == "__main__":
    ft.app(target=main)