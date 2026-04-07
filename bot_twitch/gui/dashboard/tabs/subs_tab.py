# gui/dashboard/tabs/subs_tab.py
import flet as ft
import asyncio
import threading
from datetime import datetime
from gui.dashboard.tabs.base_tab import BaseTab
from gui.styles import AppColors
from core.subs_manager import SubsManager
from core.database import db


class SubsTab(BaseTab):
    
    def __init__(self, page: ft.Page):
        super().__init__(page)
        self.subs_list = ft.Column(scroll=ft.ScrollMode.AUTO, expand=True)
        self.last_sync_text = ft.Text("", size=11, color="white60")
        self.total_subs_text = ft.Text("0", size=20, weight="bold", color=AppColors.ACCENT)
        self.loading = ft.ProgressRing(width=30, height=30, visible=False)
    
    def build(self) -> ft.Tab:
        self._load_subs()
        
        return ft.Tab(
            text="SUSCRIPCIONES",
            icon=ft.Icons.SUBSCRIPTIONS,
            content=ft.Container(
                padding=20,
                bgcolor=AppColors.BG_DARK,
                content=ft.Column([
                    ft.Container(
                        content=ft.Row([
                            ft.Column([
                                ft.Text("TOTAL SUSCRIPTORES", size=12, color="white60"),
                                self.total_subs_text,
                            ]),
                            ft.VerticalDivider(width=1, color=ft.Colors.GREY_800),
                            ft.Column([
                                ft.Text("ÚLTIMA SINCRONIZACIÓN", size=12, color="white60"),
                                self.last_sync_text,
                            ]),
                            ft.Row([
                                self.loading,
                                ft.IconButton(
                                    icon=ft.Icons.SYNC,
                                    icon_color=AppColors.ACCENT,
                                    on_click=self._sync_subs,
                                    tooltip="Sincronizar ahora"
                                ),
                            ])
                        ], alignment="spaceBetween"),
                        padding=15,
                        bgcolor=AppColors.SURFACE,
                        border_radius=10,
                        margin=ft.margin.only(bottom=20)
                    ),
                    ft.Text("LISTA DE SUSCRIPTORES", size=14, weight="bold", color=AppColors.ACCENT),
                    ft.Divider(color=ft.Colors.GREY_900),
                    self.subs_list,
                ], spacing=15, expand=True)
            )
        )
    
    def _load_subs(self):
        self.subs_list.controls.clear()
        
        try:
            subs = db.get_all_subscribers()
        except Exception as e:
            print(f"❌ Error cargando suscriptores: {e}")
            subs = []
        
        if not subs:
            self.subs_list.controls.append(
                ft.Container(
                    content=ft.Text("No hay suscriptores registrados.", color="white30"),
                    alignment=ft.alignment.center,
                    padding=40
                )
            )
            self.total_subs_text.value = "0"
            self.page.update()
            return
        
        self.total_subs_text.value = str(len(subs))
        self.last_sync_text.value = datetime.now().strftime("%d/%m/%Y %H:%M")
        
        subs_sorted = sorted(subs, key=lambda x: (x.get('tier', 0), x.get('meses', 0)), reverse=True)
        for sub in subs_sorted:
            self._add_sub_card(sub)
        
        self.page.update()
    
    def _add_sub_card(self, sub: dict):
        username = sub.get('username', '')
        tier = sub.get('tier', 1)
        meses = sub.get('meses', 1)
        fecha = sub.get('fecha', '')
        
        if tier == 3:
            tier_color = AppColors.T3_COLOR
            tier_bg = AppColors.T3_BG
            tier_label = "TIER 3"
        elif tier == 2:
            tier_color = AppColors.T2_COLOR
            tier_bg = AppColors.T2_BG
            tier_label = "TIER 2"
        else:
            tier_color = AppColors.T1_COLOR
            tier_bg = AppColors.T1_BG
            tier_label = "TIER 1"
        
        fecha_str = ""
        if fecha:
            try:
                fecha_obj = datetime.fromisoformat(fecha.replace('Z', '+00:00'))
                fecha_str = fecha_obj.strftime("%d/%m/%Y")
            except:
                fecha_str = fecha[:10] if fecha else ""
        
        card = ft.Container(
            content=ft.Row([
                ft.Icon(ft.Icons.STAR, color=tier_color, size=20),
                ft.Column([
                    ft.Text(username.upper(), weight="bold", size=14, color=ft.Colors.WHITE),
                    ft.Text(f"Desde: {fecha_str}", size=10, color="white50") if fecha_str else ft.Text("", size=10),
                ], expand=True, spacing=2),
                ft.Container(
                    content=ft.Text(f"{meses} meses", size=12, weight="bold", color=tier_color),
                    bgcolor=tier_bg,
                    border_radius=10,
                    padding=ft.padding.symmetric(horizontal=10, vertical=4)
                ),
                ft.Container(
                    content=ft.Text(tier_label, size=11, weight="bold", color=tier_color),
                    bgcolor=tier_bg,
                    border_radius=10,
                    padding=ft.padding.symmetric(horizontal=8, vertical=3)
                ),
            ]),
            padding=12,
            bgcolor=AppColors.SURFACE,
            border_radius=10,
            margin=ft.margin.only(bottom=8),
            ink=True
        )
        self.subs_list.controls.append(card)
    
    def _sync_subs(self, e):
        self.loading.visible = True
        self.page.update()
        
        def sync_in_thread():
            try:
                subs_manager = SubsManager(debug=True)
                async def do():
                    await subs_manager.actualizar_desde_twitch()
                asyncio.run(do())
                self.page.run_task(self._reload_subs)
            except Exception as e:
                print(f"❌ Error en sincronización: {e}")
                self.page.run_task(self._show_error, str(e))
        
        thread = threading.Thread(target=sync_in_thread, daemon=True)
        thread.start()
    
    async def _reload_subs(self):
        self._load_subs()
        self.loading.visible = False
        self.page.update()
        self._show_snackbar("Suscripciones sincronizadas correctamente", "green")
    
    async def _show_error(self, message: str):
        self.loading.visible = False
        self.page.update()
        self._show_snackbar(f"Error: {message}", "red")
    
    def _show_snackbar(self, message: str, color: str):
        self.page.snack_bar = ft.SnackBar(
            content=ft.Text(message),
            bgcolor=color,
            duration=3000,
        )
        self.page.snack_bar.open = True
        self.page.update()