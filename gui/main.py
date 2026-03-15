import flet as ft
import json
import os
import datetime
import subprocess
import threading
import sys
import re
import asyncio

# --- CONFIGURACIÓN DE RUTAS ---
CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
BASE_DIR = os.path.abspath(os.path.join(CURRENT_DIR, ".."))

# Forzamos a Python a incluir la raíz del proyecto para encontrar la carpeta /core
if BASE_DIR not in sys.path:
    sys.path.append(BASE_DIR)

CONFIG_PATH = os.path.join(BASE_DIR, "config.json")
BOT_SCRIPT = os.path.join(BASE_DIR, "app.py")
PHRASES_DIR = os.path.join(BASE_DIR, "phrases")
SUBS_FILE = os.path.join(BASE_DIR, "data", "subs", "subscriptores_activos.json")

# Intentamos importar el SubsManager con la ruta corregida
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
    page.title = "FANTAN BOT - Dashboard Pro Ultra"
    page.theme_mode = ft.ThemeMode.DARK
    page.window.width = 1250
    page.window.height = 900
    
    page.bot_process = None
    config_data = load_config()

    # --- COMPONENTES MONITOR ---
    terminal_messages = ft.ListView(expand=True, spacing=2, auto_scroll=True)
    chat_messages = ft.ListView(expand=True, spacing=2, auto_scroll=True)
    status_dot = ft.CircleAvatar(bgcolor=ft.Colors.RED, radius=7)
    status_text = ft.Text("DESCONECTADO", color=ft.Colors.RED_400, weight="bold")

    # --- LÓGICA LOGS Y BOT ---
    def add_log(message, color=ft.Colors.WHITE):
        now = datetime.datetime.now().strftime("%H:%M:%S")
        if message and message.strip():
            msg_clean = message.strip()
            if any(x in msg_clean for x in ["[CHAT]", "-> @", "!", "comando"]):
                chat_messages.controls.append(ft.Text(f"[{now}] {msg_clean}", color=ft.Colors.GREEN_200, size=12))
            else:
                terminal_messages.controls.append(ft.Text(f"[{now}] {msg_clean}", color=color, size=12))
            page.update()

    def clear_terminal(e):
        terminal_messages.controls.clear()
        add_log("SISTEMA: El registro de terminal ha sido vaciado.", ft.Colors.AMBER_400)
        page.update()

    def clear_chat(e):
        chat_messages.controls.clear()
        add_log("SISTEMA: El historial de Chat y Comandos ha sido vaciado.", ft.Colors.CYAN_400)
        page.update()

    def toggle_bot(e):
        if page.bot_process is None:
            try:
                env = os.environ.copy()
                env["PYTHONIOENCODING"] = "utf-8"
                page.bot_process = subprocess.Popen(
                    [sys.executable, "-u", BOT_SCRIPT], 
                    stdout=subprocess.PIPE, 
                    stderr=subprocess.STDOUT, 
                    stdin=subprocess.PIPE, 
                    text=True, 
                    cwd=BASE_DIR, 
                    env=env, 
                    encoding="utf-8"
                )
                threading.Thread(target=lambda: [add_log(line) for line in iter(page.bot_process.stdout.readline, "")], daemon=True).start()
                
                # Actualización visual: Verde
                status_dot.bgcolor = ft.Colors.GREEN
                status_text.value = "CONECTADO"
                status_text.color = ft.Colors.GREEN_400
                btn_power.text, btn_power.bgcolor = "DETENER BOT", ft.Colors.RED_700
                add_log("SISTEMA: Bot encendido correctamente.", ft.Colors.GREEN_400)
            except Exception as ex: add_log(f"ERROR: {ex}", ft.Colors.RED)
        else:
            try:
                page.bot_process.stdin.write("shutdown\n")
                page.bot_process.stdin.flush()
            except:
                page.bot_process.terminate()
            
            page.bot_process = None
            # Actualización visual: Rojo
            status_dot.bgcolor = ft.Colors.RED
            status_text.value = "DESCONECTADO"
            status_text.color = ft.Colors.RED_400
            btn_power.text, btn_power.bgcolor = "ENCENDER BOT", ft.Colors.BLUE_700
            add_log("SISTEMA: Bot detenido.", ft.Colors.ORANGE_400)
        page.update()

    # --- LÓGICA FRASES ---
    phrase_editor = ft.TextField(multiline=True, expand=True, text_size=13, bgcolor="#1a1a1a")
    var_dropdown = ft.Dropdown(label="Categoría", expand=True)
    file_list_column = ft.Column(spacing=5, scroll=ft.ScrollMode.AUTO)
    current_file_path = ft.Text("", visible=False)

    def load_phrases_from_file():
        if not current_file_path.value or not var_dropdown.value: return
        try:
            with open(current_file_path.value, "r", encoding="utf-8") as f:
                content = f.read()
            pattern = rf"{var_dropdown.value}\s*=\s*\[([\s\S]*?)\]"
            match = re.search(pattern, content)
            if match:
                phrases_raw = re.findall(r'["\']([\s\S]*?)["\']\s*(?:,|$)', match.group(1))
                phrase_editor.value = "\n".join([p.strip() for p in phrases_raw if p.strip()])
            page.update()
        except: pass

    def save_phrases_to_file(e):
        if not current_file_path.value or not var_dropdown.value: return
        try:
            with open(current_file_path.value, "r", encoding="utf-8") as f:
                content = f.read()
            new_lines = phrase_editor.value.split("\n")
            formatted_phrases = "\n    " + ",\n    ".join([f'"{line.strip()}"' for line in new_lines if line.strip()]) + "\n"
            pattern = rf"({var_dropdown.value}\s*=\s*\[)[\s\S]*?(\])"
            new_content = re.sub(pattern, rf"\1{formatted_phrases}\2", content)
            with open(current_file_path.value, "w", encoding="utf-8") as f:
                f.write(new_content)
            page.open(ft.SnackBar(ft.Text(f"✅ Guardado con éxito en {var_dropdown.value}")))
        except Exception as ex:
            page.open(ft.SnackBar(ft.Text(f"❌ Error al guardar: {ex}")))

    def select_file(path, label):
        current_file_path.value = path
        with open(path, "r", encoding="utf-8") as f:
            vars = re.findall(r'^(\w+)\s*=\s*\[', f.read(), re.MULTILINE)
        var_dropdown.options = [ft.dropdown.Option(v) for v in vars]
        var_dropdown.value = vars[0] if vars else None
        var_dropdown.on_change = lambda _: load_phrases_from_file()
        load_phrases_from_file()
        page.update()

    def build_sidebar():
        file_list_column.controls.clear()
        if os.path.exists(PHRASES_DIR):
            for folder in sorted(os.listdir(PHRASES_DIR)):
                folder_path = os.path.join(PHRASES_DIR, folder)
                if os.path.isdir(folder_path):
                    for file in sorted(os.listdir(folder_path)):
                        if file.endswith(".py") and file != "__init__.py":
                            p = os.path.join(folder_path, file)
                            display_text = f"{folder.upper()} / {file.replace('.py', '').upper()}"
                            tag_color = ft.Colors.BLUE_400
                            if "social" in folder.lower(): tag_color = ft.Colors.PINK_400
                            elif "bot" in folder.lower(): tag_color = ft.Colors.PURPLE_400
                            file_list_column.controls.append(
                                ft.Container(
                                    content=ft.Row([ft.Icon(ft.Icons.FOLDER_OPEN_ROUNDED, size=14, color=tag_color), ft.Text(display_text, size=11, weight="w500")]),
                                    padding=10, on_click=lambda e, path=p, lbl=display_text: select_file(path, lbl),
                                    ink=True, border_radius=8
                                )
                            )
        page.update()

    # --- LÓGICA SUBS CORREGIDA (Hilos + Async) ---
    subs_view_column = ft.Column(scroll=ft.ScrollMode.AUTO, expand=True)

    def run_sync_task(e):
        def sync_worker():
            async def sync():
                if SubsManager is None:
                    add_log("ERROR: No se encontró SubsManager en core/subs_manager.py", ft.Colors.RED)
                    return
                add_log("SISTEMA: Sincronizando subs con la API de Twitch...", ft.Colors.AMBER)
                try:
                    await SubsManager.actualizar_desde_twitch()
                    add_log("SISTEMA: ¡Sincronización completada!", ft.Colors.GREEN_400)
                    refresh_subs_list()
                except Exception as ex:
                    add_log(f"ERROR al sincronizar: {ex}", ft.Colors.RED)
            
            asyncio.run(sync())
        
        # Ejecutamos en un hilo separado para no congelar la app de Flet
        threading.Thread(target=sync_worker, daemon=True).start()

    def refresh_subs_list(e=None):
            subs_view_column.controls.clear()
            if os.path.exists(SUBS_FILE):
                try:
                    with open(SUBS_FILE, "r", encoding="utf-8") as f:
                        data = json.load(f)
                    
                    for user, info in sorted(data.items()):
                        tier = info.get("tier", 1)
                        meses = info.get("meses", 1) # Obtenemos los meses (por defecto 1)
                        
                        # --- LÓGICA DE FECHA Y HORA EUROPEA ---
                        fecha_iso = info.get("fecha", "")
                        try:
                            y, m, d = fecha_iso[:10].split("-")
                            hora = fecha_iso[11:16]
                            fecha_final = f"{d}/{m}/{y} ({hora}hs)"
                        except:
                            fecha_final = fecha_iso

                        color_tier = ft.Colors.PURPLE_ACCENT_100 if tier == 3 else ft.Colors.BLUE_400 if tier == 2 else ft.Colors.GREEN_400
                        bg_tier = "#2b0040" if tier == 3 else "#001a33" if tier == 2 else "#0d1a0d"

                        subs_view_column.controls.append(
                            ft.Container(
                                content=ft.Row([
                                    ft.Icon(ft.Icons.PERSON_ROUNDED, color=color_tier, size=25),
                                    ft.Column([
                                        ft.Row([
                                            ft.Text(f"@{user.upper()}", weight="bold", size=13, color=color_tier),
                                            # Etiqueta de meses
                                            ft.Container(
                                                content=ft.Text(f" {meses} MESES ", size=9, weight="bold", color=ft.Colors.BLACK),
                                                bgcolor=color_tier,
                                                border_radius=5,
                                                padding=2
                                            ) if meses > 1 else ft.Text("NUEVO", size=9, color=ft.Colors.GREY_500)
                                        ], spacing=10, vertical_alignment=ft.CrossAxisAlignment.CENTER),
                                        ft.Text(f"Suscrito: {fecha_final}", size=10, color=ft.Colors.GREY_400)
                                    ], expand=True, spacing=2),
                                    ft.Container(
                                        content=ft.Text(f"TIER {tier}", size=10, weight="bold"),
                                        padding=ft.padding.all(5),
                                        border_radius=5,
                                        bgcolor=ft.Colors.with_opacity(0.2, color_tier)
                                    )
                                ], alignment=ft.MainAxisAlignment.SPACE_BETWEEN),
                                padding=10, bgcolor=bg_tier, border_radius=10, margin=ft.margin.only(top=5), border=ft.border.all(1, "#333333")
                            )
                        )
                except Exception as ex: 
                    add_log(f"ERROR leyendo subs: {ex}", ft.Colors.RED)
            
            page.update()
            
    # --- AJUSTES ---
    def create_setting_field(label, value, config_key, sub_key=None):
        is_secret = any(x in label.lower() for x in ["key", "token", "secret", "id"])
        text_field = ft.TextField(label=label, value=str(value), height=45, text_size=12, expand=True, password=is_secret, can_reveal_password=is_secret)
        def save_indiv(e):
            if sub_key: config_data[config_key][sub_key] = text_field.value
            else: config_data[config_key] = [a.strip() for a in text_field.value.split(",")] if config_key == "admin_users" else text_field.value
            with open(CONFIG_PATH, "w", encoding="utf-8") as f: json.dump(config_data, f, indent=4)
            page.open(ft.SnackBar(ft.Text(f"✅ {label} guardado")))
        return ft.Row([text_field, ft.IconButton(ft.Icons.SAVE, on_click=save_indiv, icon_color=ft.Colors.GREEN_400)])

    ajustes_col_1 = ft.Column([ft.Text("CONEXIÓN TWITCH", weight="bold", color=ft.Colors.BLUE_400), create_setting_field("Canal", config_data["twitch"]["channel"], "twitch", "channel"), create_setting_field("Nombre Bot", config_data["twitch"]["bot_name"], "twitch", "bot_name"), create_setting_field("Broadcaster ID", config_data["twitch"]["broadcaster_id"], "twitch", "broadcaster_id"), ft.Text("TOKENS BOT", weight="bold", color=ft.Colors.PURPLE_400), create_setting_field("Token Bot", config_data["twitch"]["token_bot"], "twitch", "token_bot"), create_setting_field("Client ID Bot", config_data["twitch"]["client_id_bot"], "twitch", "client_id_bot")], expand=1, spacing=15)
    ajustes_col_2 = ft.Column([ft.Text("IA & ADMIN", weight="bold", color=ft.Colors.GREEN_400), create_setting_field("OpenAI API Key", config_data["openai"]["api_key"], "openai", "api_key"), create_setting_field("Admins", ", ".join(config_data["admin_users"]), "admin_users"), ft.Text("SEGURIDAD BROADCASTER", weight="bold", color=ft.Colors.RED_400), create_setting_field("Token Broadcaster", config_data["twitch"]["token"], "twitch", "token"), create_setting_field("Client ID Broadcaster", config_data["twitch"]["client_id"], "twitch", "client_id"), create_setting_field("Client Secret", config_data["twitch"]["client_secret"], "twitch", "client_secret")], expand=1, spacing=15)

    btn_power = ft.ElevatedButton("ENCENDER BOT", icon=ft.Icons.POWER_SETTINGS_NEW, on_click=toggle_bot, bgcolor=ft.Colors.BLUE_700, color="white", height=45)

    # --- LAYOUT PRINCIPAL ---
    page.add(
        ft.Container(padding=10, content=ft.Row([
            ft.Text("🏎️ FANTAN BOT PANEL", size=20, weight="bold"), 
            ft.Container(expand=True), 
            ft.Column([ft.Row([status_dot, status_text], spacing=10), ft.IconButton(ft.Icons.POWER_OFF_ROUNDED, icon_color=ft.Colors.RED_400, on_click=lambda _: page.window.close(), padding=0)], horizontal_alignment=ft.CrossAxisAlignment.END, spacing=5)
        ])),
        ft.Tabs(selected_index=0, expand=1, tabs=[
            ft.Tab(text="Monitor", icon=ft.Icons.TERMINAL, content=ft.Container(padding=20, content=ft.Column([
                ft.Row([
                    ft.Column([ft.Text("SISTEMA", weight="bold", size=12), ft.Container(terminal_messages, expand=True, bgcolor="#0d0d0d", padding=10, border_radius=10, border=ft.border.all(1, ft.Colors.GREY_900)), ft.Row([ft.Container(expand=True), ft.IconButton(ft.Icons.DELETE_OUTLINE, on_click=clear_terminal)])], expand=1), 
                    ft.Column([ft.Text("CHAT Y COMANDOS", weight="bold", size=12), ft.Container(chat_messages, expand=True, bgcolor="#0d0d0d", padding=10, border_radius=10, border=ft.border.all(1, ft.Colors.GREY_900)), ft.Row([ft.Container(expand=True), ft.IconButton(ft.Icons.DELETE_OUTLINE, on_click=clear_chat)])], expand=1)
                ], expand=True, spacing=20),
                ft.Row([btn_power], alignment=ft.MainAxisAlignment.CENTER)
            ]))),
            ft.Tab(text="Frases", icon=ft.Icons.EDIT_NOTE, content=ft.Row([
                ft.Container(width=220, bgcolor="#121212", content=file_list_column, padding=15), 
                ft.Container(expand=True, padding=25, content=ft.Column([ft.Row([var_dropdown, ft.ElevatedButton("GUARDAR", on_click=save_phrases_to_file, bgcolor=ft.Colors.GREEN_700)]), phrase_editor]))
            ])),
            ft.Tab(text="Subs", icon=ft.Icons.STAR, content=ft.Container(padding=20, content=ft.Column([
                ft.Row([
                    ft.Text("LISTA DE SUSCRIPTORES", weight="bold"), 
                    ft.Row([
                        ft.ElevatedButton("SINCRONIZAR TWITCH", icon=ft.Icons.SYNC, on_click=run_sync_task, bgcolor=ft.Colors.PURPLE_700, color="white"),
                        ft.IconButton(ft.Icons.REFRESH, on_click=refresh_subs_list)
                    ])
                ], alignment=ft.MainAxisAlignment.SPACE_BETWEEN), 
                subs_view_column
            ]))),
            ft.Tab(text="Ajustes", icon=ft.Icons.SETTINGS, content=ft.Container(padding=30, content=ft.Column([
                ft.Row([ajustes_col_1, ft.VerticalDivider(width=40), ajustes_col_2], expand=True, vertical_alignment=ft.CrossAxisAlignment.START)
            ], scroll=ft.ScrollMode.AUTO)))
        ])
    )
    
    build_sidebar()
    refresh_subs_list()
    page.update()

if __name__ == "__main__":
    ft.app(target=main)