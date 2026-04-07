# gui/dialogs/profile_dialog.py
import flet as ft
from gui.styles import AppColors
from gui.services.user_service import UserService


class EditProfileDialog:
    """Diálogo para editar el perfil del usuario"""
    
    def __init__(self, page: ft.Page, username: str, full_name: str, email: str, ref_code: str, on_success):
        self.page = page
        self.username = username
        self.on_success = on_success
        self.user_service = UserService()
        
        # Campos del formulario
        self.full_name_field = ft.TextField(
            label="Nombre completo",
            value=full_name,
            width=400,
            bgcolor=AppColors.SURFACE,
            color="white",
            border_color=ft.Colors.GREY_700,
            focused_border_color=AppColors.ACCENT
        )
        
        self.email_field = ft.TextField(
            label="Correo electrónico",
            value=email,
            width=400,
            bgcolor=AppColors.SURFACE,
            color="white",
            border_color=ft.Colors.GREY_700,
            focused_border_color=AppColors.ACCENT
        )
        
        self.ref_code_field = ft.TextField(
            label="Código de referencia",
            value=ref_code,
            width=400,
            bgcolor=AppColors.SURFACE,
            color="white",
            border_color=ft.Colors.GREY_700,
            focused_border_color=AppColors.ACCENT,
            disabled=True  # No editable, solo visual
        )
        
        self.password_field = ft.TextField(
            label="Nueva contraseña (dejar vacío para no cambiar)",
            password=True,
            can_reveal_password=True,
            width=400,
            bgcolor=AppColors.SURFACE,
            color="white",
            border_color=ft.Colors.GREY_700,
            focused_border_color=AppColors.ACCENT
        )
        
        self.confirm_password_field = ft.TextField(
            label="Confirmar nueva contraseña",
            password=True,
            can_reveal_password=True,
            width=400,
            bgcolor=AppColors.SURFACE,
            color="white",
            border_color=ft.Colors.GREY_700,
            focused_border_color=AppColors.ACCENT
        )
        
        self.dialog = ft.AlertDialog(
            title=ft.Text(
                f"EDITAR PERFIL - {username.upper()}",
                size=18,
                weight="bold",
                color=AppColors.ACCENT
            ),
            content=ft.Container(
                content=ft.Column([
                    self.full_name_field,
                    self.email_field,
                    self.ref_code_field,
                    ft.Divider(color=ft.Colors.GREY_800),
                    ft.Text("CAMBIAR CONTRASEÑA", size=12, weight="bold", color="white60"),
                    self.password_field,
                    self.confirm_password_field,
                ], spacing=15, scroll=ft.ScrollMode.AUTO),
                width=450,
                height=450,
                padding=10
            ),
            actions=[
                ft.TextButton("CANCELAR", on_click=self._close),
                ft.ElevatedButton(
                    "GUARDAR",
                    bgcolor=AppColors.ACCENT,
                    color="white",
                    on_click=self._save
                )
            ],
            actions_alignment=ft.MainAxisAlignment.END
        )
    
    def open(self):
        """Abre el diálogo"""
        self.page.open(self.dialog)
        self.page.update()
    
    def _close(self, e):
        """Cierra el diálogo"""
        self.page.close(self.dialog)
        self.page.update()
    
    def _save(self, e):
        """Guarda los cambios"""
        # Validar contraseñas
        new_password = self.password_field.value
        confirm_password = self.confirm_password_field.value
        
        if new_password and new_password != confirm_password:
            self._show_error("Las contraseñas no coinciden")
            return
        
        if new_password and len(new_password) < 6:
            self._show_error("La contraseña debe tener al menos 6 caracteres")
            return
        
        # Actualizar perfil
        success = self.user_service.update_profile(
            username=self.username,
            name=self.full_name_field.value,
            email=self.email_field.value,
            password=new_password if new_password else None,
            ref_code=self.ref_code_field.value
        )
        
        if success:
            self._close(e)
            self.on_success()
        else:
            self._show_error("Error al actualizar el perfil")
    
    def _show_error(self, message: str):
        """Muestra mensaje de error"""
        self.page.snack_bar = ft.SnackBar(
            content=ft.Text(message),
            bgcolor=ft.Colors.RED_400,
            duration=3000,
        )
        self.page.snack_bar.open = True
        self.page.update()