# gui/dialogs/user_dialog.py
import flet as ft
from gui.styles import AppColors
from gui.services.user_service import UserService


class RegisterDialog:
    """Diálogo para registro de nuevos usuarios"""
    
    def __init__(self, page: ft.Page, on_success=None):
        self.page = page
        self.on_success = on_success  # Puede ser None
        self.user_service = UserService()
        
        # Campos del formulario
        self.username_field = ft.TextField(
            label="Nombre de usuario *",
            width=400,
            bgcolor=AppColors.SURFACE,
            color="white",
            border_color=ft.Colors.GREY_700,
            focused_border_color=AppColors.ACCENT
        )
        
        self.password_field = ft.TextField(
            label="Contraseña *",
            password=True,
            can_reveal_password=True,
            width=400,
            bgcolor=AppColors.SURFACE,
            color="white",
            border_color=ft.Colors.GREY_700,
            focused_border_color=AppColors.ACCENT
        )
        
        self.confirm_password_field = ft.TextField(
            label="Confirmar contraseña *",
            password=True,
            can_reveal_password=True,
            width=400,
            bgcolor=AppColors.SURFACE,
            color="white",
            border_color=ft.Colors.GREY_700,
            focused_border_color=AppColors.ACCENT
        )
        
        self.full_name_field = ft.TextField(
            label="Nombre completo",
            width=400,
            bgcolor=AppColors.SURFACE,
            color="white",
            border_color=ft.Colors.GREY_700,
            focused_border_color=AppColors.ACCENT
        )
        
        self.email_field = ft.TextField(
            label="Correo electrónico",
            width=400,
            bgcolor=AppColors.SURFACE,
            color="white",
            border_color=ft.Colors.GREY_700,
            focused_border_color=AppColors.ACCENT
        )
        
        self.dialog = ft.AlertDialog(
            title=ft.Text(
                "REGISTRAR NUEVA CUENTA",
                size=18,
                weight="bold",
                color=AppColors.ACCENT
            ),
            content=ft.Container(
                content=ft.Column([
                    self.username_field,
                    self.password_field,
                    self.confirm_password_field,
                    self.full_name_field,
                    self.email_field,
                    ft.Text(
                        "* Campos obligatorios",
                        size=10,
                        color="white60",
                        italic=True
                    ),
                ], spacing=15),
                width=450,
                height=450,
                padding=10
            ),
            actions=[
                ft.TextButton("CANCELAR", on_click=self._close),
                ft.ElevatedButton(
                    "REGISTRARSE",
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
        """Registra el nuevo usuario"""
        username = self.username_field.value
        password = self.password_field.value
        confirm_password = self.confirm_password_field.value
        full_name = self.full_name_field.value
        email = self.email_field.value
        
        # Validaciones
        if not username or not password:
            self._show_error("Usuario y contraseña son obligatorios")
            return
        
        if password != confirm_password:
            self._show_error("Las contraseñas no coinciden")
            return
        
        if len(password) < 6:
            self._show_error("La contraseña debe tener al menos 6 caracteres")
            return
        
        # Registrar usuario (tier 1 por defecto)
        success = self.user_service.register(
            username=username,
            password=password,
            full_name=full_name or "",
            email=email or "",
            tier=1
        )
        
        if success:
            self._close(e)
            # Verificar si on_success existe antes de llamarlo
            if self.on_success and callable(self.on_success):
                self.on_success()
            self._show_success(f"Cuenta {username} creada correctamente. ¡Ya puedes iniciar sesión!")
        else:
            self._show_error(f"Error al crear la cuenta. El usuario {username} ya existe.")
    
    def _show_error(self, message: str):
        """Muestra mensaje de error"""
        self.page.snack_bar = ft.SnackBar(
            content=ft.Text(message),
            bgcolor=ft.Colors.RED_400,
            duration=3000,
        )
        self.page.snack_bar.open = True
        self.page.update()
    
    def _show_success(self, message: str):
        """Muestra mensaje de éxito"""
        self.page.snack_bar = ft.SnackBar(
            content=ft.Text(message),
            bgcolor=ft.Colors.GREEN_400,
            duration=3000,
        )
        self.page.snack_bar.open = True
        self.page.update()


class CreateUserDialog:
    """Diálogo para crear un nuevo usuario (admin)"""
    
    def __init__(self, page: ft.Page, on_success=None):
        self.page = page
        self.on_success = on_success  # Puede ser None
        self.user_service = UserService()
        
        # Campos del formulario
        self.username_field = ft.TextField(
            label="Nombre de usuario *",
            width=400,
            bgcolor=AppColors.SURFACE,
            color="white",
            border_color=ft.Colors.GREY_700,
            focused_border_color=AppColors.ACCENT
        )
        
        self.password_field = ft.TextField(
            label="Contraseña *",
            password=True,
            can_reveal_password=True,
            width=400,
            bgcolor=AppColors.SURFACE,
            color="white",
            border_color=ft.Colors.GREY_700,
            focused_border_color=AppColors.ACCENT
        )
        
        self.full_name_field = ft.TextField(
            label="Nombre completo",
            width=400,
            bgcolor=AppColors.SURFACE,
            color="white",
            border_color=ft.Colors.GREY_700,
            focused_border_color=AppColors.ACCENT
        )
        
        self.email_field = ft.TextField(
            label="Correo electrónico",
            width=400,
            bgcolor=AppColors.SURFACE,
            color="white",
            border_color=ft.Colors.GREY_700,
            focused_border_color=AppColors.ACCENT
        )
        
        self.tier_dropdown = ft.Dropdown(
            label="Rol",
            width=400,
            value="1",
            options=[
                ft.dropdown.Option("1", "Gratuito"),
                ft.dropdown.Option("2", "Suscripción"),
                ft.dropdown.Option("3", "Admin"),
            ],
            bgcolor=AppColors.SURFACE,
            color="white",
            border_color=ft.Colors.GREY_700
        )
        
        self.dialog = ft.AlertDialog(
            title=ft.Text(
                "CREAR NUEVO USUARIO",
                size=18,
                weight="bold",
                color=AppColors.ACCENT
            ),
            content=ft.Container(
                content=ft.Column([
                    self.username_field,
                    self.password_field,
                    self.full_name_field,
                    self.email_field,
                    self.tier_dropdown,
                ], spacing=15),
                width=450,
                padding=10
            ),
            actions=[
                ft.TextButton("CANCELAR", on_click=self._close),
                ft.ElevatedButton(
                    "CREAR",
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
        """Crea el usuario"""
        username = self.username_field.value
        password = self.password_field.value
        full_name = self.full_name_field.value
        email = self.email_field.value
        tier = int(self.tier_dropdown.value)
        
        # Validaciones
        if not username or not password:
            self._show_error("Usuario y contraseña son obligatorios")
            return
        
        if len(password) < 6:
            self._show_error("La contraseña debe tener al menos 6 caracteres")
            return
        
        # Crear usuario
        success = self.user_service.register(
            username=username,
            password=password,
            full_name=full_name,
            email=email,
            tier=tier
        )
        
        if success:
            self._close(e)
            # Verificar si on_success existe antes de llamarlo
            if self.on_success and callable(self.on_success):
                self.on_success()
            self._show_success(f"Usuario {username} creado correctamente")
        else:
            self._show_error(f"Error al crear usuario {username}. ¿Ya existe?")
    
    def _show_error(self, message: str):
        """Muestra mensaje de error"""
        self.page.snack_bar = ft.SnackBar(
            content=ft.Text(message),
            bgcolor=ft.Colors.RED_400,
            duration=3000,
        )
        self.page.snack_bar.open = True
        self.page.update()
    
    def _show_success(self, message: str):
        """Muestra mensaje de éxito"""
        self.page.snack_bar = ft.SnackBar(
            content=ft.Text(message),
            bgcolor=ft.Colors.GREEN_400,
            duration=3000,
        )
        self.page.snack_bar.open = True
        self.page.update()


class EditUserDialog:
    """Diálogo para editar un usuario (solo admin)"""
    
    def __init__(self, page: ft.Page, username: str, full_name: str, email: str, ref_code: str, on_success=None):
        self.page = page
        self.username = username
        self.on_success = on_success  # Puede ser None
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
            focused_border_color=AppColors.ACCENT
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
        
        self.tier_dropdown = ft.Dropdown(
            label="Rol",
            width=400,
            options=[
                ft.dropdown.Option("1", "Gratuito"),
                ft.dropdown.Option("2", "Suscripción"),
                ft.dropdown.Option("3", "Admin"),
            ],
            bgcolor=AppColors.SURFACE,
            color="white",
            border_color=ft.Colors.GREY_700
        )
        
        self.dialog = ft.AlertDialog(
            title=ft.Text(
                f"EDITAR USUARIO - {username.upper()}",
                size=18,
                weight="bold",
                color=AppColors.ACCENT
            ),
            content=ft.Container(
                content=ft.Column([
                    ft.Text(f"Usuario: {username}", size=14, color="white60"),
                    ft.Divider(color=ft.Colors.GREY_800),
                    self.full_name_field,
                    self.email_field,
                    self.ref_code_field,
                    self.tier_dropdown,
                    ft.Divider(color=ft.Colors.GREY_800),
                    ft.Text("CAMBIAR CONTRASEÑA", size=12, weight="bold", color="white60"),
                    self.password_field,
                ], spacing=15, scroll=ft.ScrollMode.AUTO),
                width=450,
                height=500,
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
        # Cargar el tier actual del usuario
        profile = self.user_service.get_profile(self.username)
        if profile:
            self.tier_dropdown.value = str(profile.get("tier", 1))
        self.page.open(self.dialog)
        self.page.update()
    
    def _close(self, e):
        """Cierra el diálogo"""
        self.page.close(self.dialog)
        self.page.update()
    
    def _save(self, e):
        """Guarda los cambios"""
        # Validar contraseña
        new_password = self.password_field.value
        if new_password and len(new_password) < 6:
            self._show_error("La contraseña debe tener al menos 6 caracteres")
            return
        
        # Actualizar usuario
        success = self.user_service.update_user(
            username=self.username,
            full_name=self.full_name_field.value,
            email=self.email_field.value,
            ref_code=self.ref_code_field.value,
            password=new_password if new_password else None,
            tier=int(self.tier_dropdown.value)
        )
        
        if success:
            self._close(e)
            # Verificar si on_success existe antes de llamarlo
            if self.on_success and callable(self.on_success):
                self.on_success()
            self._show_success("Usuario actualizado correctamente")
        else:
            self._show_error("Error al actualizar el usuario")
    
    def _show_error(self, message: str):
        """Muestra mensaje de error"""
        self.page.snack_bar = ft.SnackBar(
            content=ft.Text(message),
            bgcolor=ft.Colors.RED_400,
            duration=3000,
        )
        self.page.snack_bar.open = True
        self.page.update()
    
    def _show_success(self, message: str):
        """Muestra mensaje de éxito"""
        self.page.snack_bar = ft.SnackBar(
            content=ft.Text(message),
            bgcolor=ft.Colors.GREEN_400,
            duration=3000,
        )
        self.page.snack_bar.open = True
        self.page.update()