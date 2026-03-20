import flet as ft
import json
import os
import datetime
import subprocess
import threading
import sys
import re
import asyncio

# --- FIX DE RUTAS PARA MÓDULOS ---
CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
BASE_DIR = os.path.abspath(os.path.join(CURRENT_DIR, ".."))
if BASE_DIR not in sys.path:
    sys.path.insert(0, BASE_DIR)

# --- IMPORTACIÓN DE COMPONENTES MODULARES ---
from gui.components.monitor_tab import build_monitor_tab
from gui.components.phrases_tab import build_phrases_tab
from gui.components.subs_tab import build_subs_tab
from gui.components.settings_tab import build_settings_tab
from gui.styles import AppColors, AppStyles

# --- CONFIGURACIÓN DE RUTAS ---
CONFIG_PATH = os.path.join(BASE_DIR, "config.json")
BOT_SCRIPT = os.path.join(BASE_DIR, "app.py")
PHRASES_DIR = os.path.join(BASE_DIR, "phrases")
SUBS_FILE = os.path.join(BASE_DIR, "data", "subs", "subscriptores_activos.json")

try:
    from core.subs_manager import SubsManager
    print("✅ SubsManager cargado correctamente.")
except ImportError as e:
    print(f"❌ Error al importar SubsManager: {e}")
    SubsManager = None

def load_config():
    base_config = {
        "openai": {"api_key": ""}, 
        "twitch": {
            "token": "", "channel": "", "bot_name": "", 
            "client_id": "", "client_secret": "", "bot_id": "", 
            "client_id_bot": "", "token_bot": "", "broadcaster_id": ""
        }, 
        "admin_users": []
    }
    if os.path.exists(CONFIG_PATH):
        try:
            with open(CONFIG_PATH, "r", encoding="utf-8") as f:
                existing = json.load(f)
                if "openai" in existing: base_config["openai"].update(existing["openai"])
                if "twitch" in existing: base_config["twitch"].update(existing["twitch"])
                if "admin_users" in existing: base_config["admin_users"] = existing["admin_users"]
        except: pass
    return base_config

def main(page: ft.Page):
    page.title = "BOT - Dashboard Pro Ultra"
    page.theme_mode = ft.ThemeMode.DARK
    page.window.width = 1250
    page.window.height = 900
    page.bot_process = None
    config_data = load_config()

    # --- REFERENCIAS DE UI ---
    terminal_messages = ft.ListView(expand=True, spacing=2, auto_scroll=True)
    chat_messages = ft.ListView(expand=True, spacing=2, auto_scroll=True)
    status_dot = ft.CircleAvatar(bgcolor=ft.Colors.RED, radius=7)
    status_text = ft.Text("DESCONECTADO", color=ft.Colors.RED_400, weight="bold")
    phrase_editor = ft.TextField(multiline=True, expand=True, text_size=13, bgcolor="#1a1a1a")
    var_dropdown = ft.Dropdown(label="Categoría", expand=True)
    file_list_column = ft.Column(spacing=5, scroll=ft.ScrollMode.AUTO)
    current_file_path = ft.Text("", visible=False)
    subs_view_column = ft.Column(scroll=ft.ScrollMode.AUTO, expand=True)

    # --- LÓGICA DE LOGS Y BOT ---
    def add_log(message, color=ft.Colors.WHITE):
        now = datetime.datetime.now().strftime("%H:%M:%S")
        if message and message.strip():
            msg_clean = message.strip()
            if any(x in msg_clean for x in ["[CHAT]", "-> @", "!", "comando"]):
                chat_messages.controls.append(ft.Text(f"[{now}] {msg_clean}", color=ft.Colors.GREEN_200, size=12))
            else:
                terminal_messages.controls.append(ft.Text(f"[{now}] {msg_clean}", color=color, size=12))
            page.update()

    def toggle_bot(e):
        if page.bot_process is None:
            try:
                env = os.environ.copy()
                env["PYTHONIOENCODING"] = "utf-8"
                page.bot_process = subprocess.Popen(
                    [sys.executable, "-u", BOT_SCRIPT], 
                    stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True, 
                    cwd=BASE_DIR, env=env, encoding="utf-8"
                )
                threading.Thread(target=lambda: [add_log(line) for line in iter(page.bot_process.stdout.readline, "")], daemon=True).start()
                status_dot.bgcolor = ft.Colors.GREEN
                status_text.value, status_text.color = "CONECTADO", ft.Colors.GREEN_400
                btn_power.text, btn_power.bgcolor = "DETENER BOT", ft.Colors.RED_700
                add_log("SISTEMA: Bot encendido.", ft.Colors.GREEN_400)
            except Exception as ex: add_log(f"ERROR: {ex}", ft.Colors.RED)
        else:
            page.bot_process.terminate()
            page.bot_process = None
            status_dot.bgcolor = ft.Colors.RED
            status_text.value, status_text.color = "DESCONECTADO", ft.Colors.RED_400
            btn_power.text, btn_power.bgcolor = "ENCENDER BOT", ft.Colors.BLUE_700
            add_log("SISTEMA: Bot detenido.", ft.Colors.ORANGE_400)
        page.update()

    # --- LÓGICA DE FRASES ---
    def load_phrases():
        if not current_file_path.value or not var_dropdown.value: return
        with open(current_file_path.value, "r", encoding="utf-8") as f:
            content = f.read()
            match = re.search(rf"{var_dropdown.value}\s*=\s*\[([\s\S]*?)\]", content)
            if match:
                phrases = re.findall(r'["\']([\s\S]*?)["\']', match.group(1))
                phrase_editor.value = "\n".join([p.strip() for p in phrases])
        page.update()

    def save_phrases(e):
        with open(current_file_path.value, "r", encoding="utf-8") as f: content = f.read()
        fmt = "\n    " + ",\n    ".join([f'"{l.strip()}"' for l in phrase_editor.value.split("\n") if l.strip()]) + "\n"
        new_content = re.sub(rf"({var_dropdown.value}\s*=\s*\[)[\s\S]*?(\])", rf"\1{fmt}\2", content)
        with open(current_file_path.value, "w", encoding="utf-8") as f: f.write(new_content)
        page.open(ft.SnackBar(ft.Text("✅ Guardado correctamente")))

    def select_file(path, label):
        current_file_path.value = path
        with open(path, "r", encoding="utf-8") as f:
            vars = re.findall(r'^(\w+)\s*=\s*\[', f.read(), re.MULTILINE)
        var_dropdown.options = [ft.dropdown.Option(v) for v in vars]
        var_dropdown.value = vars[0] if vars else None
        var_dropdown.on_change = lambda _: load_phrases()
        load_phrases()

    def build_sidebar():
        file_list_column.controls.clear()
        if os.path.exists(PHRASES_DIR):
            for folder in sorted(os.listdir(PHRASES_DIR)):
                f_path = os.path.join(PHRASES_DIR, folder)
                if os.path.isdir(f_path):
                    for file in [f for f in os.listdir(f_path) if f.endswith(".py") and f != "__init__.py"]:
                        p = os.path.join(f_path, file)
                        display_text = f"{folder.upper()} / {file.replace('.py', '').upper()}"
                        file_list_column.controls.append(ft.Container(
                            content=ft.Row([ft.Icon(ft.Icons.FOLDER_OPEN_ROUNDED, size=14), ft.Text(display_text, size=11)]),
                            on_click=lambda e, path=p: select_file(path, ""), padding=10, ink=True, border_radius=8
                        ))
        page.update()

    # --- LÓGICA DE SUBS ---
    def refresh_subs_list(e=None):
        subs_view_column.controls.clear()
        if os.path.exists(SUBS_FILE):
            try:
                with open(SUBS_FILE, "r", encoding="utf-8") as f:
                    data = json.load(f)
                
                for user, info in sorted(data.items()):
                    tier = info.get("tier", 1)
                    meses = info.get("meses", 1)
                    fecha_iso = info.get("fecha", "")
                    try:
                        y, m, d = fecha_iso[:10].split("-")
                        hora = fecha_iso[11:16]
                        fecha_final = f"{d}/{m}/{y} ({hora}hs)"
                    except:
                        fecha_final = fecha_iso

                    color_tier = AppColors.T3_COLOR if tier == 3 else AppColors.T2_COLOR if tier == 2 else AppColors.T1_COLOR
                    style_data = AppStyles.sub_card(tier)

                    subs_view_column.controls.append(
                        ft.Container(
                            content=ft.Row([
                                ft.Icon(ft.Icons.PERSON_ROUNDED, color=color_tier, size=25),
                                ft.Column([
                                    ft.Row([
                                        ft.Text(f"@{user.upper()}", weight="bold", size=13, color=color_tier),
                                        ft.Container(
                                            content=ft.Text(f" {meses} MESES ", size=9, weight="bold", color=ft.Colors.BLACK),
                                            bgcolor=color_tier, border_radius=5, padding=2
                                        ) if meses > 1 else ft.Text("NUEVO", size=9, color=ft.Colors.GREY_500)
                                    ], spacing=10, vertical_alignment=ft.CrossAxisAlignment.CENTER),
                                    ft.Text(f"Suscrito: {fecha_final}", size=10, color=ft.Colors.GREY_400)
                                ], expand=True, spacing=2),
                                ft.Container(
                                    content=ft.Text(f"TIER {tier}", size=10, weight="bold"),
                                    padding=5, border_radius=5, bgcolor=ft.Colors.with_opacity(0.2, color_tier)
                                )
                            ], alignment=ft.MainAxisAlignment.SPACE_BETWEEN),
                            **style_data
                        )
                    )
            except Exception as ex: 
                add_log(f"ERROR leyendo subs: {ex}", ft.Colors.RED)
        page.update()

    def run_sync_task(e):
        def sync_worker():
            async def sync():
                if SubsManager:
                    add_log("SISTEMA: Sincronizando con Twitch...", ft.Colors.AMBER)
                    await SubsManager.actualizar_desde_twitch()
                    refresh_subs_list()
                    add_log("SISTEMA: Sincronización completada.", ft.Colors.GREEN_400)
            asyncio.run(sync())
        threading.Thread(target=sync_worker, daemon=True).start()

    # --- LÓGICA DE AJUSTES ---
    def save_setting(config_key, sub_key, value):
        if sub_key: config_data[config_key][sub_key] = value
        else:
            if config_key == "admin_users":
                config_data[config_key] = [a.strip() for a in value.split(",")]
            else:
                config_data[config_key] = value
        with open(CONFIG_PATH, "w", encoding="utf-8") as f:
            json.dump(config_data, f, indent=4)
        page.open(ft.SnackBar(ft.Text("✅ Ajuste guardado")))

    btn_power = ft.ElevatedButton("ENCENDER BOT", icon=ft.Icons.POWER_SETTINGS_NEW, on_click=toggle_bot, bgcolor=ft.Colors.BLUE_700, color="white", height=45)

    # --- CONSTRUCCIÓN FINAL DEL LAYOUT ---
# --- CONSTRUCCIÓN FINAL DEL LAYOUT ---
    page.add(
        ft.Container(
            padding=ft.padding.only(left=20, right=20, top=10, bottom=10),
            content=ft.Row([
                # LADO IZQUIERDO: Título principal
                ft.Row([
                    ft.Icon(ft.Icons.SPEED_ROUNDED, color=AppColors.ACCENT, size=30),
                    ft.Text("BOT PANEL", size=24, weight="bold"), 
                ], spacing=15),
                
                ft.Container(expand=True), # Espacio flexible en el centro
                
                # LADO DERECHO: Salir arriba, Estado abajo
                ft.Column([
                    # Botón de Salir (ENCIMA)
                    ft.TextButton(
                        content=ft.Row([
                            ft.Text("SALIR DE LA APP", size=11, weight="bold"),
                            ft.Icon(ft.Icons.LOGOUT_ROUNDED, size=16),
                        ], spacing=8),
                        style=ft.ButtonStyle(
                            color=ft.Colors.RED_400,
                        ),
                        on_click=lambda _: page.window.close(),
                    ),
                    
                    # Indicador de Estado (DEBAJO)
                    ft.Container(
                        content=ft.Row([
                            status_dot, 
                            status_text
                        ], spacing=10),
                        padding=ft.padding.only(right=5) # Ajuste fino para alinear con el icono de arriba
                    )
                ], 
                horizontal_alignment=ft.CrossAxisAlignment.END, # Alinea todo al borde derecho
                spacing=0 # Sin espacio excesivo entre ambos
                )
            ], alignment=ft.MainAxisAlignment.SPACE_BETWEEN)
        ),
        
        # Tabs de la aplicación
        ft.Tabs(
            expand=1, 
            tabs=[
                build_monitor_tab(terminal_messages, chat_messages, btn_power, lambda _: terminal_messages.controls.clear(), lambda _: chat_messages.controls.clear()),
                build_phrases_tab(file_list_column, var_dropdown, phrase_editor, save_phrases),
                build_subs_tab(subs_view_column, run_sync_task, refresh_subs_list),
                build_settings_tab(config_data, save_setting)
            ]
        )
    ) 
    build_sidebar()
    refresh_subs_list()
    page.update()

if __name__ == "__main__":
    ft.app(target=main)