import flet as ft
import datetime
from gui.styles import AppColors
from gui.dashboard.header import DashboardHeader
from gui.dashboard.bot_controller import BotController
from core.database import db

class Dashboard:
    """Dashboard principal"""
    
    def __init__(self, page: ft.Page, username: str, tier: int, on_logout):
        self.page = page
        self.username = username
        self.tier = tier
        self.on_logout = on_logout
        self.bot_controller = BotController(page)
        
        # Estado compartido
        self.logs = ft.ListView(expand=True, spacing=2, auto_scroll=True)
        self.chat_logs = ft.ListView(expand=True, spacing=2, auto_scroll=True)
        self.bot_status = ft.CircleAvatar(bgcolor=ft.Colors.RED, radius=7)
        self.bot_status_text = ft.Text("DESCONECTADO", color=ft.Colors.RED_400, weight="bold")
    
    # --- 🟢 NUEVA FUNCIÓN: NOTIFICACIONES TIPO TOAST 🟢 ---
    def show_toast(self, message: str, icon, color: str):
        self.page.snack_bar = ft.SnackBar(
            content=ft.Row([
                ft.Icon(icon, color=ft.Colors.WHITE, size=20),
                ft.Text(message, weight="w500")
            ], spacing=10),
            bgcolor=color,
            behavior=ft.SnackBarBehavior.FLOATING,
            shape=ft.RoundedRectangleBorder(radius=10),
            margin=ft.margin.all(20),
            duration=2000,
        )
        self.page.snack_bar.open = True
        self.page.update()

    def build(self):
        """Construye el dashboard"""
        self.page.clean()
        
        btn_power = self.bot_controller.build_button(
            self.bot_status,
            self.bot_status_text,
            self._add_log
        )
        
        header = DashboardHeader(
            self.username,
            self.tier,
            self.bot_status,
            self.bot_status_text,
            self.on_logout
        ).build()
        
        tabs_control = ft.Tabs(
            expand=1,
            tabs=self._build_tabs(),
            animation_duration=300,
            selected_index=0,
        )
        
        tabs_with_button = ft.Stack(
            controls=[
                tabs_control,
                ft.Container(
                    content=btn_power,
                    right=15,
                    top=14,
                    height=40,
                )
            ],
            expand=True
        )
        
        self.page.add(header, tabs_with_button)

        # --- 🔵 SORPRESA 1: LOG DE BIENVENIDA CON GRADIENTE 🔵 ---
        self.logs.controls.append(
            ft.Container(
                content=ft.Text(f"🚀 Sesión iniciada: {self.username.upper()}", color=ft.Colors.WHITE, weight="bold"),
                padding=10,
                border_radius=8,
                gradient=ft.LinearGradient(
                    begin=ft.alignment.top_left,
                    end=ft.alignment.bottom_right,
                    colors=[ft.Colors.PURPLE_800, ft.Colors.BLUE_800],
                ),
                margin=ft.margin.only(bottom=10)
            )
        )
        
        if self.tier < 3 and not db.is_user_setup_done(self.username):
            from gui.dialogs.setup_dialog import SetupDialog
            SetupDialog(self.page, self.username).open()
                
        self.page.update()

    def _add_log(self, message: str, is_chat: bool = False):
        now = datetime.datetime.now().strftime("%H:%M:%S")
        target = self.chat_logs if is_chat else self.logs
        color = ft.Colors.GREEN_200 if is_chat else ft.Colors.WHITE
        target.controls.append(ft.Text(f"[{now}] {message}", color=color, size=12))
        self.page.update()

    # --- 🟡 SORPRESA 2: LIMPIEZA CON FEEDBACK VISUAL 🟡 ---
    def _clear_logs(self, e):
        self.logs.controls.clear()
        self.show_toast("Registros de SISTEMA borrados", ft.Icons.DELETE_SWEEP_OUTLINED, ft.Colors.RED_800)

    def _clear_chat(self, e):
        self.chat_logs.controls.clear()
        self.show_toast("Historial de CHAT vaciado", ft.Icons.CLEAN_HANDS_OUTLINED, ft.Colors.GREEN_800)

    def _build_tabs(self):
        from gui.dashboard.tabs.monitor_tab import build_monitor_tab
        from gui.dashboard.tabs.phrases_tab import PhrasesTab
        from gui.dashboard.tabs.subs_tab import SubsTab
        from gui.dashboard.tabs.profile_tab import ProfileTab
        from gui.dashboard.tabs.settings_tab import SettingsTab
        from gui.dashboard.tabs.admin_tab import AdminTab
        
        tabs = []
        tabs.append(build_monitor_tab(self.logs, self.chat_logs, self._clear_logs, self._clear_chat))
        
        if self.tier >= 2:
            tabs.append(PhrasesTab(self.page).build())
        else:
            tabs.append(self._locked_tab("FRASES", "TIER 2"))
            
        if self.tier >= 2:
            tabs.append(SubsTab(self.page).build())
        else:
            tabs.append(self._locked_tab("SUBS", "TIER 2"))
        
        if self.tier >= 3:
            tabs.append(AdminTab(self.page, self.username).build())
        else:
            tabs.append(self._locked_tab("ADMIN", "TIER 3"))
        
        tabs.append(ProfileTab(self.page, self.username, self.tier).build())
        tabs.append(SettingsTab(self.page).build())
        return tabs

    def _locked_tab(self, title: str, required: str):
        return ft.Tab(
            text=title, 
            icon=ft.Icons.LOCK, 
            content=ft.Container(
                alignment=ft.alignment.center, 
                content=ft.Text(f"Bloqueado: Requiere {required}")
            )
        )