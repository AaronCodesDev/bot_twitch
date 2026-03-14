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
CONFIG_PATH = os.path.join(BASE_DIR, "config.json")
BOT_SCRIPT = os.path.join(BASE_DIR, "app.py")
PHRASES_DIR = os.path.join(BASE_DIR, "phrases")
PROMPT_PATH = os.path.join(BASE_DIR, "core", "prompt.py")

# --- LÓGICA DE CARGA ---

def load_config():
    base_config = {"openai": {"api_key": ""}, "twitch": {"token": "", "channel": "", "bot_name": "", "client_id": "", "client_secret": "", "bot_id": "", "client_id_bot": "", "token_bot": "", "broadcaster_id": ""}, "admin_users": []}
    if os.path.exists(CONFIG_PATH):
        try:
            with open(CONFIG_PATH, "r", encoding="utf-8") as f:
                existing = json.load(f)
                if "openai" in existing: base_config["openai"].update(existing["openai"])
                if "twitch" in existing: base_config["twitch"].update(existing["twitch"])
                if "admin_users" in existing: base_config["admin_users"] = existing["admin_users"]
        except: pass
    return base_config

# --- INTERFAZ PRINCIPAL ---

def main(page: ft.Page):
    page.title = "FANTAN BOT - Dashboard"
    page.theme_mode = ft.ThemeMode.DARK
    page.window.width = 1150
    page.window.height = 900
    
    page.bot_process = None
    config_data = load_config()

    # --- COMPONENTES UI ---
    status_dot = ft.CircleAvatar(bgcolor=ft.Colors.RED, radius=7)
    status_text = ft.Text("DESCONECTADO", color=ft.Colors.RED_400, weight="bold")
    terminal_messages = ft.ListView(expand=True, spacing=2, auto_scroll=True)
    
    # Celdas de Personalidad Individuales
    prompt_base = ft.TextField(label="SYSTEM_BASE (Público General)", multiline=True, min_lines=3)
    prompt_sub = ft.TextField(label="SYSTEM_SUB (Suscriptores)", multiline=True, min_lines=3)
    prompt_fav = ft.TextField(label="SYSTEM_FAVORITO (Favoritos)", multiline=True, min_lines=3)
    
    # Editor de Frases
    phrase_editor = ft.TextField(multiline=True, expand=True, text_size=13, bgcolor="#1a1a1a")
    var_dropdown = ft.Dropdown(label="Categoría", expand=True)
    file_list_column = ft.Column(spacing=5, scroll=ft.ScrollMode.AUTO)
    current_file_path = ft.Text("", visible=False)

    # --- LÓGICA DE FUNCIONES ---

    def load_prompts_from_file():
        if os.path.exists(PROMPT_PATH):
            with open(PROMPT_PATH, "r", encoding="utf-8") as f:
                content = f.read()
                # Extraer contenido entre comillas usando regex
                b = re.search(r'SYSTEM_BASE\s*=\s*"(.*?)"', content)
                s = re.search(r'SYSTEM_SUB\s*=\s*"(.*?)"', content)
                f_fav = re.search(r'SYSTEM_FAVORITO\s*=\s*"(.*?)"', content)
                
                prompt_base.value = b.group(1) if b else ""
                prompt_sub.value = s.group(1) if s else ""
                prompt_fav.value = f_fav.group(1) if f_fav else ""
        page.update()

    def save_prompts_action(e):
        os.makedirs(os.path.dirname(PROMPT_PATH), exist_ok=True)
        with open(PROMPT_PATH, "w", encoding="utf-8") as f:
            f.write(f'SYSTEM_BASE = "{prompt_base.value}"\n')
            f.write(f'SYSTEM_SUB = "{prompt_sub.value}"\n')
            f.write(f'SYSTEM_FAVORITO = "{prompt_fav.value}"\n\n')
            f.write('def get_system_message(nivel: str) -> str:\n    if nivel == "suscriptor": return SYSTEM_SUB\n')
            f.write('    elif nivel == "favorito": return SYSTEM_FAVORITO\n    return SYSTEM_BASE\n\n')
            f.write('def build_user_message(user: str, contexto: str, texto: str) -> str:\n')
            f.write('    return (f"Diálogo previo con @{user}:\\n{contexto}\\n\\n" f"Mensaje actual: \\"{texto}\\"\\n" "⚠️ Responde en UNA sola frase corta y sarcástica.")\n')
        page.open(ft.SnackBar(ft.Text("🧠 Personalidad guardada con éxito")))

    def load_phrases_from_file():
        if not current_file_path.value or not var_dropdown.value: return
        with open(current_file_path.value, "r", encoding="utf-8") as f:
            content = f.read()
        pattern = rf"{var_dropdown.value}\s*=\s*\[([\s\S]*?)\]"
        match = re.search(pattern, content)
        if match:
            phrases_raw = re.findall(r'["\']([\s\S]*?)["\']\s*(?:,|$)', match.group(1))
            clean = [re.sub(r'\s+', ' ', p.replace("\n", " ").strip()) for p in phrases_raw if p.strip()]
            phrase_editor.value = "\n".join(clean)
        page.update()

    def save_phrases_action(e):
        if not current_file_path.value or not var_dropdown.value: return
        lines = phrase_editor.value.split("\n")
        phrases_to_save = [f'    "{l.strip().replace(chr(34), "\\\"")}"' for l in lines if l.strip()]
        new_block = f"{var_dropdown.value} = [\n" + ",\n".join(phrases_to_save) + "\n]"
        with open(current_file_path.value, "r", encoding="utf-8") as f:
            content = f.read()
        pattern = rf"{var_dropdown.value}\s*=\s*\[.*?\]"
        updated = re.sub(pattern, new_block, content, flags=re.DOTALL)
        with open(current_file_path.value, "w", encoding="utf-8") as f:
            f.write(updated)
        page.open(ft.SnackBar(ft.Text("✅ Frases guardadas")))

    def select_file(path, label):
        current_file_path.value = path
        with open(path, "r", encoding="utf-8") as f:
            vars = re.findall(r'^(\w+)\s*=\s*\[', f.read(), re.MULTILINE)
        var_dropdown.options = [ft.dropdown.Option(v) for v in vars]
        var_dropdown.value = vars[0] if vars else None
        var_dropdown.on_change = lambda _: load_phrases_from_file()
        load_phrases_from_file()
        page.update()

    def toggle_bot(e):
        if page.bot_process is None:
            try:
                for d in ['data/users', 'data/subs', 'data/save', 'data/backup']: 
                    os.makedirs(os.path.join(BASE_DIR, d), exist_ok=True)
                page.bot_process = subprocess.Popen([sys.executable, "-u", BOT_SCRIPT], stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True, cwd=BASE_DIR)
                threading.Thread(target=lambda: [add_log(line) for line in iter(page.bot_process.stdout.readline, "")], daemon=True).start()
                status_dot.bgcolor, status_text.value = ft.Colors.GREEN, "CONECTADO"
                btn_power.text, btn_power.bgcolor = "DETENER BOT", ft.Colors.RED_700
            except Exception as ex: add_log(f"ERROR: {ex}", ft.Colors.RED)
        else:
            page.bot_process.terminate()
            page.bot_process = None
            status_dot.bgcolor, status_text.value = ft.Colors.RED, "DESCONECTADO"
            btn_power.text, btn_power.bgcolor = "ENCENDER BOT", ft.Colors.BLUE_700
        page.update()

    def add_log(message, color=ft.Colors.WHITE):
        now = datetime.datetime.now().strftime("%H:%M:%S")
        if message and message.strip():
            terminal_messages.controls.append(ft.Text(f"[{now}] {message.strip()}", color=color, size=12))
            page.update()

    def open_wizard(e):
        curr = load_config()
        w_fields = {
            "api_key": ft.TextField(label="OpenAI Key", value=curr["openai"]["api_key"], password=True, can_reveal_password=True),
            "token_bot": ft.TextField(label="Token Bot", value=curr["twitch"]["token_bot"], password=True),
            "client_id_bot": ft.TextField(label="Client ID Bot", value=curr["twitch"]["client_id_bot"]),
            "channel": ft.TextField(label="Channel", value=curr["twitch"]["channel"]),
            "bot_name": ft.TextField(label="Bot Name", value=curr["twitch"]["bot_name"]),
            "token": ft.TextField(label="Token Broadcaster", value=curr["twitch"]["token"], password=True),
            "client_id": ft.TextField(label="Client ID Broadcaster", value=curr["twitch"]["client_id"]),
            "broadcaster_id": ft.TextField(label="Broadcaster ID", value=curr["twitch"]["broadcaster_id"]),
            "admins": ft.TextField(label="Admins (separados por coma)", value=", ".join(curr["admin_users"]))
        }
        def save_and_close(e):
            config_data["openai"]["api_key"] = w_fields["api_key"].value
            for k in ["token_bot", "client_id_bot", "channel", "bot_name", "token", "client_id", "broadcaster_id"]:
                config_data["twitch"][k] = w_fields[k].value
            config_data["admin_users"] = [a.strip() for a in w_fields["admins"].value.split(",") if a.strip()]
            with open(CONFIG_PATH, "w", encoding="utf-8") as f:
                json.dump(config_data, f, indent=4, ensure_ascii=False)
            page.close(wizard_dialog)
            page.update()

        wizard_dialog = ft.AlertDialog(
            title=ft.Text("Ajustes"),
            content=ft.Column([f for f in w_fields.values()], tight=True, scroll=ft.ScrollMode.AUTO, height=500),
            actions=[ft.TextButton("Cancelar", on_click=lambda _: page.close(wizard_dialog)), ft.ElevatedButton("Guardar", on_click=save_and_close)]
        )
        page.open(wizard_dialog)

    def build_sidebar():
        file_list_column.controls.clear()
        if os.path.exists(PHRASES_DIR):
            for root, _, files in os.walk(PHRASES_DIR):
                for file in files:
                    if file.endswith(".py") and file != "__init__.py":
                        p = os.path.join(root, file)
                        l = os.path.relpath(p, PHRASES_DIR)
                        file_list_column.controls.append(ft.Container(content=ft.Row([ft.Icon(ft.Icons.CODE, size=16), ft.Text(l.upper(), size=11)]), padding=10, on_click=lambda e, path=p, lbl=l: select_file(path, lbl), ink=True))

    btn_power = ft.ElevatedButton("ENCENDER BOT", icon=ft.Icons.POWER_SETTINGS_NEW, on_click=toggle_bot, bgcolor=ft.Colors.BLUE_700, color="white", height=50)

    page.add(
        ft.Container(padding=10, content=ft.Row([ft.Text("🏎️ FANTAN BOT PANEL", size=20, weight="bold"), ft.Container(expand=True), status_dot, status_text])),
        ft.Tabs(selected_index=0, expand=1, tabs=[
            ft.Tab(text="Monitor", icon=ft.Icons.TERMINAL, content=ft.Container(padding=20, content=ft.Column([ft.Container(content=terminal_messages, expand=True, bgcolor="#0d0d0d", padding=10, border_radius=10), ft.Row([ft.IconButton(ft.Icons.DELETE_SWEEP, on_click=lambda _: terminal_messages.controls.clear()), ft.Container(expand=True), btn_power])]))),
            ft.Tab(text="Frases", icon=ft.Icons.EDIT_NOTE, content=ft.Row([ft.Container(width=220, bgcolor="#121212", content=file_list_column, padding=15), ft.Container(expand=True, padding=25, content=ft.Column([ft.Row([var_dropdown, ft.ElevatedButton("GUARDAR", on_click=save_phrases_action, bgcolor=ft.Colors.GREEN_700)]), phrase_editor]))])),
            ft.Tab(text="Personalidad", icon=ft.Icons.PSYCHOLOGY, content=ft.Container(padding=25, content=ft.Column([
                ft.Row([ft.Text("Define el comportamiento del Bot", weight="bold"), ft.Container(expand=True), ft.ElevatedButton("GUARDAR PERSONALIDAD", icon=ft.Icons.SAVE, on_click=save_prompts_action, bgcolor=ft.Colors.BLUE_700)]),
                ft.Divider(),
                prompt_base,
                prompt_sub,
                prompt_fav
            ], spacing=20))),
            ft.Tab(text="Ajustes", icon=ft.Icons.SETTINGS, content=ft.Container(padding=40, content=ft.Column([ft.ElevatedButton("ABRIR WIZARD DE CONFIGURACIÓN", icon=ft.Icons.SETTINGS_SUGGEST, on_click=open_wizard, height=60, bgcolor=ft.Colors.PURPLE_800)], horizontal_alignment=ft.CrossAxisAlignment.CENTER)))
        ])
    )
    
    build_sidebar()
    load_prompts_from_file() # Cargar los textos al iniciar
    page.update()

if __name__ == "__main__":
    ft.app(target=main)