import flet as ft
import subprocess
import threading
import sys
import os

BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
BOT_SCRIPT = os.path.join(BASE_DIR, "app.py")

class BotController:
    """Controlador del bot (iniciar/detener)"""
    
    def __init__(self, page: ft.Page):
        self.page = page
        self.bot_process = None
    
    def build_button(self, status_dot, status_text, on_log):
        """Construye el botón de control"""
        self.status_dot = status_dot
        self.status_text = status_text
        self.on_log = on_log
        
        self.btn = ft.ElevatedButton(
            "ENCENDER BOT",
            icon=ft.Icons.POWER_SETTINGS_NEW,
            on_click=self._toggle,
            bgcolor=ft.Colors.BLUE_700,
            color="white",
            height=45
        )
        return self.btn
    
    def _toggle(self, e):
        """Alterna el estado del bot"""
        if self.bot_process is None:
            self._start()
        else:
            self._stop()
    
    def _start(self):
        """Inicia el bot"""
        try:
            env = os.environ.copy()
            env["PYTHONIOENCODING"] = "utf-8"
            
            self.bot_process = subprocess.Popen(
                [sys.executable, "-u", BOT_SCRIPT],
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                text=True,
                cwd=BASE_DIR,
                env=env,
                encoding="utf-8"
            )
            
            def read_output():
                for line in iter(self.bot_process.stdout.readline, ""):
                    if line.strip():
                        is_chat = any(x in line for x in ["[CHAT]", "-> @", "!", "comando"])
                        self.on_log(line.strip(), is_chat)
            
            threading.Thread(target=read_output, daemon=True).start()
            
            self.status_dot.bgcolor = ft.Colors.GREEN
            self.status_text.value = "CONECTADO"
            self.status_text.color = ft.Colors.GREEN_400
            self.btn.text = "DETENER BOT"
            self.btn.bgcolor = ft.Colors.RED_700
            
        except Exception as ex:
            self.on_log(f"ERROR: {ex}", False)
        
        self.page.update()
    
    def _stop(self):
        """Detiene el bot"""
        if self.bot_process:
            self.bot_process.terminate()
            self.bot_process = None
        
        self.status_dot.bgcolor = ft.Colors.RED
        self.status_text.value = "DESCONECTADO"
        self.status_text.color = ft.Colors.RED_400
        self.btn.text = "ENCENDER BOT"
        self.btn.bgcolor = ft.Colors.BLUE_700
        self.page.update()