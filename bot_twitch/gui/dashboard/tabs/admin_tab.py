# gui/dashboard/tabs/admin_tab.py (versión corregida)
import flet as ft
from gui.dashboard.tabs.base_tab import BaseTab
from gui.styles import AppColors
from gui.services.user_service import UserService
from gui.dialogs.user_dialog import CreateUserDialog, EditUserDialog


class AdminTab(BaseTab):
    """Pestaña de administración de usuarios"""
    
    def __init__(self, page: ft.Page, current_user: str):
        super().__init__(page)
        self.current_user = current_user
        self.user_service = UserService()
        self.user_list = ft.Column(scroll=ft.ScrollMode.AUTO, expand=True)
    
    def build(self) -> ft.Tab:
        # Cargar usuarios
        self._load_users()
        
        return ft.Tab(
            text="ADMIN",
            icon=ft.Icons.ADMIN_PANEL_SETTINGS,
            content=ft.Container(
                padding=20,
                bgcolor=AppColors.BG_DARK,
                content=ft.Column([
                    ft.Row([
                        ft.Text("USUARIOS DEL SISTEMA", size=16, weight="bold", color=AppColors.ACCENT),
                        ft.Row([
                            ft.IconButton(
                                ft.Icons.PERSON_ADD,
                                on_click=self._open_create_dialog,
                                tooltip="Crear nuevo usuario",
                                icon_color=ft.Colors.GREEN_400
                            ),
                            ft.IconButton(
                                ft.Icons.REFRESH,
                                on_click=lambda _: self._load_users(),
                                tooltip="Recargar lista"
                            )
                        ])
                    ], alignment="spaceBetween"),
                    ft.Divider(color=ft.Colors.GREY_900),
                    self.user_list
                ], spacing=15, expand=True)
            )
        )
    
    def _load_users(self):
        """Carga y muestra la lista de usuarios"""
        self.user_list.controls.clear()
        users = self.user_service.get_all_users()
        
        if not users:
            self.user_list.controls.append(
                ft.Container(
                    content=ft.Text("No hay usuarios registrados.", color="white30"),
                    alignment=ft.alignment.center,
                    padding=40
                )
            )
            self.page.update()
            return
        
        # users es una lista de tuplas (username, full_name, tier, ref_code)
        for user_data in users:
            if len(user_data) == 4:
                username, full_name, tier, ref_code = user_data
            else:
                print(f"⚠️ Formato inesperado: {user_data}")
                continue
                
            self._add_user_card(username, full_name, tier, ref_code)
        
        self.page.update()
    
    def _add_user_card(self, username: str, full_name: str, tier: int, ref_code: str):
        """Añade una tarjeta de usuario a la lista"""
        # Obtener colores según tier
        if tier == 3:
            tier_color = AppColors.T3_COLOR
            tier_bg = AppColors.T3_BG
            tier_label = "ADMIN"
        elif tier == 2:
            tier_color = AppColors.T2_COLOR
            tier_bg = AppColors.T2_BG
            tier_label = "SUSCRIPCIÓN"
        else:
            tier_color = AppColors.T1_COLOR
            tier_bg = AppColors.T1_BG
            tier_label = "GRATUITO"
        
        show_delete = username.lower() != self.current_user.lower()
        
        card = ft.Container(
            content=ft.Row([
                ft.Icon(ft.Icons.PERSON, color=tier_color, size=24),
                ft.Column([
                    ft.Text(username.upper(), weight="bold", size=14, color=ft.Colors.WHITE),
                    ft.Text(full_name or "Sin nombre", size=11, color="white50"),
                ], expand=True, spacing=2),
                ft.Container(
                    content=ft.Text(f" {ref_code or '---'} ", size=10, weight="bold", color="black"),
                    bgcolor=AppColors.ACCENT,
                    border_radius=5,
                    padding=3
                ),
                ft.VerticalDivider(width=1, color=ft.Colors.GREY_700),
                ft.Container(
                    content=ft.Text(tier_label, size=11, weight="bold", color=tier_color),
                    bgcolor=tier_bg,
                    border_radius=10,
                    padding=ft.padding.symmetric(horizontal=8, vertical=3)
                ),
                ft.Row([
                    ft.IconButton(
                        icon=ft.Icons.EDIT,
                        icon_color=AppColors.ACCENT,
                        on_click=lambda e, u=username: self._open_edit_dialog(u),
                        tooltip="Editar usuario"
                    ),
                    ft.IconButton(
                        icon=ft.Icons.DELETE,
                        icon_color=ft.Colors.RED_400,
                        on_click=lambda e, u=username: self._confirm_delete(u),
                        tooltip="Eliminar usuario",
                        visible=show_delete
                    )
                ], spacing=0)
            ]),
            padding=12,
            bgcolor=AppColors.SURFACE,
            border_radius=10,
            margin=ft.margin.only(bottom=8),
            ink=True
        )
        
        self.user_list.controls.append(card)
    
    def _open_create_dialog(self, e):
        """Abre diálogo para crear usuario"""
        dialog = CreateUserDialog(self.page, self._load_users)
        dialog.open()
    
    def _open_edit_dialog(self, username: str):
        """Abre diálogo para editar usuario"""
        # Usar get_profile que devuelve diccionario
        profile = self.user_service.get_profile(username)
        
        if profile and isinstance(profile, dict):
            # Extraer datos del diccionario
            full_name = profile.get("full_name", "")
            email = profile.get("email", "")
            ref_code = profile.get("ref_code", "")
            
            dialog = EditUserDialog(
                self.page, 
                username, 
                full_name, 
                email, 
                ref_code, 
                self._load_users
            )
            dialog.open()
        else:
            self._show_snackbar("Error: Usuario no encontrado", "red")
    
    def _confirm_delete(self, username: str):
        """Confirma eliminación de usuario"""
        
        def close_dialog(e):
            self.page.close(delete_dialog)
            
        def do_delete(e):
            success, message = self.user_service.delete_user(username, self.current_user)
            if success:
                self._show_snackbar(message, "green")
                self._load_users()
            else:
                self._show_snackbar(message, "red")
            self.page.close(delete_dialog)
        
        delete_dialog = ft.AlertDialog(
            title=ft.Text("CONFIRMAR ELIMINACIÓN", size=18, weight="bold"),
            content=ft.Text(
                f"¿Estás seguro de que quieres eliminar al usuario {username.upper()}?\n\n"
                f"Esta acción no se puede deshacer.",
                size=14
            ),
            actions=[
                ft.TextButton("CANCELAR", on_click=close_dialog),
                ft.ElevatedButton(
                    "ELIMINAR",
                    bgcolor=ft.Colors.RED_700,
                    color="white",
                    on_click=do_delete
                )
            ]
        )
        
        self.page.open(delete_dialog)
    
    def _show_snackbar(self, message: str, color: str):
        """Muestra un mensaje temporal"""
        self.page.snack_bar = ft.SnackBar(
            content=ft.Text(message),
            bgcolor=color,
            duration=3000,
        )
        self.page.snack_bar.open = True
        self.page.update()