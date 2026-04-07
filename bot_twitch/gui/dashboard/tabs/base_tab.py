import flet as ft

class BaseTab:
    """Clase base para todas las pestañas"""
    
    def __init__(self, page: ft.Page):
        self.page = page
    
    def build(self) -> ft.Tab:
        """Construye la pestaña - debe ser implementado por las subclases"""
        raise NotImplementedError
    
    def _show_snackbar(self, message: str, color: str):
        """Muestra un snackbar"""
        self.page.open(ft.SnackBar(ft.Text(message), bgcolor=color))
        self.page.update()