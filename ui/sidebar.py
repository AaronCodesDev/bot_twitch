# ui/sidebar.py
# Sidebar de navegación lateral — FanTan Hub  (Redesign v2)

import flet as ft
from ui.colors import *


NAV_ITEMS = [
    {
        "id":       "home",
        "icon":     ft.Icons.GRID_VIEW_ROUNDED,
        "icon_sel": ft.Icons.GRID_VIEW_ROUNDED,
        "label":    "Hub",
        "accent":   CYAN,
    },
    {
        "id":       "twitch",
        "icon":     ft.Icons.CHAT_BUBBLE_OUTLINE_ROUNDED,
        "icon_sel": ft.Icons.CHAT_BUBBLE_ROUNDED,
        "label":    "Twitch Bot",
        "accent":   PURPLE,
    },
    {
        "id":       "tracker",
        "icon":     ft.Icons.SPEED_OUTLINED,
        "icon_sel": ft.Icons.SPEED,
        "label":    "iR Tracker",
        "accent":   ORANGE,
    },
    {
        "id":       "career",
        "icon":     ft.Icons.EMOJI_EVENTS_OUTLINED,
        "icon_sel": ft.Icons.EMOJI_EVENTS_ROUNDED,
        "label":    "iR Career",
        "accent":   GREEN,
    },
]

# IDs que aparecen en la sección inferior del sidebar
BOTTOM_ITEMS = [
    {
        "id":     "console",
        "icon":   ft.Icons.TERMINAL_ROUNDED,
        "label":  "Consola",
        "accent": CYAN,
    },
    {
        "id":     "settings",
        "icon":   ft.Icons.SETTINGS_OUTLINED,
        "label":  "Ajustes",
        "accent": MUTED,
    },
]


class Sidebar:
    def __init__(self, on_nav, initial: str = "home", on_open_console=None):
        self.on_nav           = on_nav
        self.on_open_console  = on_open_console
        self.current          = initial
        self._btns: dict[str, ft.Container] = {}
        self._built  = False

    # ─── Botón de nav principal ───────────────────────────────────────────────
    def _nav_btn(self, item: dict) -> ft.Container:
        is_sel = item["id"] == self.current
        accent = item["accent"]

        indicator = ft.Container(
            width=3, height=28,
            bgcolor=accent,
            border_radius=ft.border_radius.only(top_right=3, bottom_right=3),
            visible=is_sel,
        )

        icon_bg = ft.Container(
            content=ft.Icon(
                item["icon_sel"] if is_sel else item["icon"],
                size=18,
                color=accent if is_sel else MUTED,
            ),
            width=34, height=34,
            bgcolor=with_alpha(accent, 0.15) if is_sel else "transparent",
            border_radius=10,
            alignment=ft.Alignment(0, 0),
        )

        label = ft.Text(
            item["label"], size=11,
            color=accent if is_sel else MUTED,
            weight=ft.FontWeight.W_700 if is_sel else ft.FontWeight.W_400,
        )

        btn = ft.Container(
            content=ft.Row([
                indicator,
                ft.Container(
                    content=ft.Row([icon_bg, label], spacing=10),
                    expand=True,
                    padding=ft.padding.only(left=8, right=8),
                ),
            ], spacing=0),
            height=46,
            bgcolor=with_alpha(accent, 0.07) if is_sel else "transparent",
            border_radius=10,
            on_click=lambda e, nid=item["id"]: self._handle_click(nid),
            animate=ft.Animation(130, ft.AnimationCurve.EASE_OUT),
            margin=ft.margin.symmetric(horizontal=6, vertical=2),
        )
        return btn

    # ─── Botón inferior (Consola / Ajustes) ───────────────────────────────────
    def _bottom_btn(self, item: dict) -> ft.Container:
        is_sel = item["id"] == self.current
        accent = item["accent"]

        indicator = ft.Container(
            width=3, height=22,
            bgcolor=accent,
            border_radius=ft.border_radius.only(top_right=3, bottom_right=3),
            visible=is_sel,
        )

        icon_bg = ft.Container(
            content=ft.Icon(item["icon"], size=15,
                            color=accent if is_sel else MUTED),
            width=30, height=30,
            bgcolor=with_alpha(accent, 0.12) if is_sel else SURFACE2,
            border_radius=9,
            alignment=ft.Alignment(0, 0),
        )

        label = ft.Text(
            item["label"], size=10,
            color=accent if is_sel else MUTED,
            weight=ft.FontWeight.W_600 if is_sel else ft.FontWeight.W_400,
        )

        btn = ft.Container(
            content=ft.Row([
                indicator,
                ft.Container(
                    content=ft.Row([icon_bg, label], spacing=8),
                    expand=True,
                    padding=ft.padding.only(left=6, right=8),
                ),
            ], spacing=0),
            height=40,
            bgcolor=with_alpha(accent, 0.06) if is_sel else "transparent",
            border_radius=10,
            on_click=lambda e, nid=item["id"]: self._handle_click(nid),
            animate=ft.Animation(130, ft.AnimationCurve.EASE_OUT),
            margin=ft.margin.symmetric(horizontal=6, vertical=1),
        )
        return btn

    # ─── Click / Refresh ──────────────────────────────────────────────────────
    def _handle_click(self, nav_id: str):
        # La consola abre un diálogo, no navega
        if nav_id == "console":
            if self.on_open_console:
                self.on_open_console()
            return
        self.current = nav_id
        self._refresh()
        self.on_nav(nav_id)

    def _refresh(self):
        if not self._built:
            return

        all_items = NAV_ITEMS + BOTTOM_ITEMS
        for item in all_items:
            btn = self._btns.get(item["id"])
            if not btn:
                continue

            is_sel = item["id"] == self.current
            accent = item["accent"]

            row       = btn.content                  # Row([indicator, container])
            indicator = row.controls[0]
            inner_row = row.controls[1].content      # Row([icon_bg, label])
            icon_bg   = inner_row.controls[0]
            icon_ctrl = icon_bg.content
            label     = inner_row.controls[1]

            indicator.visible = is_sel

            # Actualizar icon_bg
            icon_bg.bgcolor = with_alpha(accent, 0.15 if item in NAV_ITEMS else 0.12) \
                if is_sel else ("transparent" if item in NAV_ITEMS else SURFACE2)

            # Actualizar icono
            if "icon_sel" in item:
                icon_ctrl.name = item["icon_sel"] if is_sel else item["icon"]
            icon_ctrl.color = accent if is_sel else MUTED

            # Actualizar label
            label.color  = accent if is_sel else MUTED
            label.weight = ft.FontWeight.W_700 if is_sel else ft.FontWeight.W_400

            # Actualizar fondo del btn
            btn.bgcolor = with_alpha(accent, 0.07 if item in NAV_ITEMS else 0.06) \
                if is_sel else "transparent"

    # ─── Build ────────────────────────────────────────────────────────────────
    def build(self) -> ft.Container:
        # Construir todos los botones
        for item in NAV_ITEMS:
            self._btns[item["id"]] = self._nav_btn(item)
        for item in BOTTOM_ITEMS:
            self._btns[item["id"]] = self._bottom_btn(item)

        self._built = True

        # Logo / marca
        logo = ft.Container(
            content=ft.Column([
                ft.Container(
                    content=ft.Stack([
                        ft.Container(
                            width=44, height=44,
                            bgcolor=with_alpha(CYAN, 0.12),
                            border_radius=14,
                            border=ft.border.all(1, with_alpha(CYAN, 0.3)),
                        ),
                        ft.Container(
                            content=ft.Text("FH", size=15,
                                            weight=ft.FontWeight.W_900, color=TEXT),
                            alignment=ft.Alignment(0, 0),
                            width=44, height=44,
                        ),
                    ]),
                    width=44, height=44,
                ),
                ft.Text("FanTan Hub", size=11, color=TEXT, weight=ft.FontWeight.W_700),
                ft.Text("v1.0", size=9, color=MUTED),
            ], spacing=5, horizontal_alignment=ft.CrossAxisAlignment.CENTER),
            padding=ft.padding.symmetric(vertical=22),
        )

        # Separador con label
        def section_label(text: str) -> ft.Container:
            return ft.Container(
                content=ft.Text(text.upper(), size=9, color=MUTED2,
                                weight=ft.FontWeight.W_600),
                padding=ft.padding.only(left=18, top=10, bottom=4),
            )

        nav_section = ft.Column([
            section_label("Navegación"),
            *[self._btns[item["id"]] for item in NAV_ITEMS],
        ], spacing=0)

        bottom_section = ft.Column([
            ft.Container(
                content=ft.Divider(height=1, color=BORDER2),
                padding=ft.padding.symmetric(horizontal=12),
            ),
            ft.Container(height=4),
            *[self._btns[item["id"]] for item in BOTTOM_ITEMS],
            ft.Container(height=8),
        ], spacing=0)

        return ft.Container(
            content=ft.Column([
                logo,
                ft.Container(
                    content=ft.Divider(height=1, color=BORDER),
                    padding=ft.padding.symmetric(horizontal=10),
                ),
                ft.Container(height=6),
                nav_section,
                ft.Container(expand=True),
                bottom_section,
            ], spacing=0, expand=True),
            width=188,
            bgcolor=SURFACE,
            border=ft.border.only(right=ft.BorderSide(1, BORDER2)),
        )
