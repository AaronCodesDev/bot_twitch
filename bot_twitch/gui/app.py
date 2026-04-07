import flet as ft
from gui.auth.login_screen import LoginScreen
from gui.dashboard.dashboard import Dashboard

class TwitchBotApp:
    """Aplicación principal del dashboard"""
    
    def __init__(self, page: ft.Page):
        self.page = page
        self._setup_page()
        self.current_user = None
        self.current_tier = None
        self.bot_process = None
    
    def _setup_page(self):
        """Configura la página principal"""
        self.page.title = "Twitch Bot - Dashboard Pro"
        self.page.theme_mode = ft.ThemeMode.DARK
        self.page.window.width = 1280
        self.page.window.height = 900
        self.page.window.min_width = 1024
        self.page.window.min_height = 768
        self.page.padding = 0
        self.page.spacing = 0
    
    def run(self):
        """Inicia la aplicación"""
        self._show_login()
    
    def _show_login(self):
        """Muestra la pantalla de login"""
        self.page.clean()
        login_screen = LoginScreen(self.page, self._on_login_success)
        login_screen.show()
    
    def _on_login_success(self, username: str, tier: int):
        """Callback cuando el login es exitoso"""
        self.current_user = username
        self.current_tier = tier
        self._show_dashboard()
    
    def _show_dashboard(self):
        """Muestra el dashboard principal"""
        self.page.clean()
        dashboard = Dashboard(
            self.page,
            self.current_user,
            self.current_tier,
            self._on_logout
        )
        dashboard.build()
    
    def _on_logout(self):
        """Callback cuando se cierra sesión"""
        if self.bot_process:
            try:
                self.bot_process.terminate()
            except:
                pass
            self.bot_process = None
        self._show_login()
    
    def stop(self):
        """Detiene la aplicación"""
        if self.bot_process:
            try:
                self.bot_process.terminate()
            except:
                pass