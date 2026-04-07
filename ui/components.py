# ui/components.py
# Componentes reutilizables — FanTan Hub

import flet as ft
from ui.colors import *


# ─── Tarjeta base ─────────────────────────────────────────────────────────────
def card(content, padding=16, expand=False, height=None, width=None, bgcolor=SURFACE, border_color=BORDER2):
    return ft.Container(
        content=content,
        bgcolor=bgcolor,
        border_radius=14,
        padding=ft.padding.all(padding),
        border=ft.border.all(1, border_color),
        expand=expand,
        height=height,
        width=width,
    )


# ─── Tarjeta de estadística ───────────────────────────────────────────────────
def stat_card(label: str, value: str, icon: str, accent: str = CYAN,
              sub_text: str = "", sub_positive: bool = True, expand: bool = True):
    sub_widget = ft.Container(height=0)
    if sub_text:
        sub_color = with_alpha(accent, 0.7)
        sub_widget = ft.Text(sub_text, size=10, color=sub_color)

    return ft.Container(
        content=ft.Row([
            ft.Container(
                content=ft.Text(icon, size=16),
                width=32, height=32,
                bgcolor=with_alpha(accent, 0.12),
                border_radius=9,
                alignment=ft.Alignment(0, 0),
            ),
            ft.Column([
                ft.Text(value, size=20, weight=ft.FontWeight.W_700, color=TEXT),
                ft.Text(label.upper(), size=9, color=MUTED, weight=ft.FontWeight.W_600),
                sub_widget,
            ], spacing=1, tight=True),
        ], spacing=10, vertical_alignment=ft.CrossAxisAlignment.CENTER),
        bgcolor=SURFACE,
        border_radius=12,
        padding=ft.padding.symmetric(horizontal=14, vertical=10),
        border=ft.border.all(1, with_alpha(accent, 0.15)),
        expand=expand,
    )


# ─── Badge ────────────────────────────────────────────────────────────────────
def badge(text: str, color: str = CYAN, small: bool = False):
    size = 10 if small else 11
    return ft.Container(
        content=ft.Text(text, size=size, color="white", weight=ft.FontWeight.W_600),
        bgcolor=with_alpha(color, 0.9),
        border_radius=20,
        padding=ft.padding.symmetric(horizontal=10 if not small else 8, vertical=3),
    )


# ─── Badge outline ────────────────────────────────────────────────────────────
def badge_outline(text: str, color: str = CYAN):
    return ft.Container(
        content=ft.Text(text, size=10, color=color, weight=ft.FontWeight.W_600),
        border=ft.border.all(1, color),
        border_radius=20,
        padding=ft.padding.symmetric(horizontal=8, vertical=2),
    )


# ─── Título de sección ────────────────────────────────────────────────────────
def section_title(title: str, subtitle: str = "", accent: str = CYAN):
    controls = [
        ft.Row([
            ft.Container(width=3, height=20, bgcolor=accent, border_radius=2),
            ft.Text(title, size=16, weight=ft.FontWeight.W_700, color=TEXT),
        ], spacing=10),
    ]
    if subtitle:
        controls.append(ft.Text(subtitle, size=12, color=MUTED))
    return ft.Column(controls, spacing=4)


# ─── Divider ──────────────────────────────────────────────────────────────────
def divider():
    return ft.Divider(height=1, color=BORDER2)


# ─── Status indicator ─────────────────────────────────────────────────────────
def status_dot(color: str = SUCCESS, size: float = 8):
    return ft.Container(
        width=size, height=size,
        bgcolor=color, border_radius=size / 2,
    )


# ─── Chip ────────────────────────────────────────────────────────────────────
def chip(label: str, icon: str = None, accent: str = CYAN, selected: bool = False):
    content_items = []
    if icon:
        content_items.append(ft.Text(icon, size=13))
    content_items.append(ft.Text(label, size=12, color=accent if selected else MUTED,
                                  weight=ft.FontWeight.W_500))
    return ft.Container(
        content=ft.Row(content_items, spacing=6),
        bgcolor=with_alpha(accent, 0.12) if selected else SURFACE2,
        border=ft.border.all(1, with_alpha(accent, 0.3) if selected else BORDER),
        border_radius=20,
        padding=ft.padding.symmetric(horizontal=14, vertical=6),
    )


# ─── Fila de info ─────────────────────────────────────────────────────────────
def info_row(label: str, value: str, value_color: str = TEXT):
    return ft.Row([
        ft.Text(label, size=12, color=MUTED, expand=True),
        ft.Text(value, size=12, color=value_color, weight=ft.FontWeight.W_500),
    ])


# ─── Barra de progreso con label ──────────────────────────────────────────────
def progress_bar_labeled(label: str, pct: float, color: str = CYAN, value_text: str = ""):
    return ft.Row([
        ft.Text(label, size=11, color=MUTED, width=140),
        ft.ProgressBar(value=pct, color=color, bgcolor=SURFACE3,
                       height=5, expand=True, border_radius=3),
        ft.Text(value_text, size=11, color=color, width=50,
                text_align=ft.TextAlign.RIGHT),
    ], spacing=10)


# ─── Log item ─────────────────────────────────────────────────────────────────
def log_item(time_str: str, message: str, level: str = "info"):
    colors = {"info": CYAN, "success": SUCCESS, "warning": WARNING, "error": DANGER}
    icons  = {"info": "●", "success": "●", "warning": "●", "error": "●"}
    c = colors.get(level, MUTED)
    return ft.Container(
        content=ft.Row([
            ft.Container(width=6, height=6, bgcolor=c, border_radius=3),
            ft.Text(f"[{time_str}]", size=11, color=MUTED, width=60),
            ft.Text(message, size=11, color=TEXT, expand=True),
        ], spacing=8),
        padding=ft.padding.symmetric(horizontal=10, vertical=5),
        border_radius=6,
    )


# ─── Botón primario ───────────────────────────────────────────────────────────
def primary_button(text: str, icon=None, accent: str = CYAN,
                   on_click=None, width=None, expand=False):
    content_items = []
    if icon:
        content_items.append(ft.Icon(icon, size=16, color="white"))
    content_items.append(ft.Text(text, size=13, color="white", weight=ft.FontWeight.W_600))

    return ft.ElevatedButton(
        content=ft.Row(content_items, spacing=8, tight=True),
        bgcolor=accent,
        color="white",
        on_click=on_click,
        width=width,
        expand=expand,
        style=ft.ButtonStyle(
            shape=ft.RoundedRectangleBorder(radius=10),
            elevation=0,
            overlay_color=with_alpha("#ffffff", 0.1),
        ),
    )


# ─── Botón secundario ─────────────────────────────────────────────────────────
def secondary_button(text: str, icon=None, accent: str = CYAN,
                     on_click=None, width=None, expand=False):
    content_items = []
    if icon:
        content_items.append(ft.Icon(icon, size=16, color=accent))
    content_items.append(ft.Text(text, size=13, color=accent, weight=ft.FontWeight.W_600))

    return ft.OutlinedButton(
        content=ft.Row(content_items, spacing=8, tight=True),
        on_click=on_click,
        width=width,
        expand=expand,
        style=ft.ButtonStyle(
            side=ft.BorderSide(1, with_alpha(accent, 0.6)),
            shape=ft.RoundedRectangleBorder(radius=10),
            color=accent,
            overlay_color=with_alpha(accent, 0.08),
        ),
    )


# ─── Header de módulo ─────────────────────────────────────────────────────────
def module_header(icon_text: str, title: str, subtitle: str = "",
                  accent: str = CYAN, actions: list = None):
    right = ft.Row(actions or [], spacing=8)
    return ft.Container(
        content=ft.Row([
            ft.Container(
                content=ft.Text(icon_text, size=22),
                width=46, height=46,
                bgcolor=with_alpha(accent, 0.12),
                border_radius=12,
                alignment=ft.Alignment(0, 0),
            ),
            ft.Column([
                ft.Text(title, size=18, weight=ft.FontWeight.W_700, color=TEXT),
                ft.Text(subtitle, size=12, color=MUTED) if subtitle else ft.Container(height=0),
            ], spacing=1, expand=True),
            right,
        ], spacing=14),
        padding=ft.padding.symmetric(horizontal=0, vertical=4),
    )


# ─── Tabla simple ─────────────────────────────────────────────────────────────
def simple_table(headers: list, rows: list, accent: str = CYAN):
    header_cells = [
        ft.Container(
            content=ft.Text(h, size=10, color=MUTED, weight=ft.FontWeight.W_600),
            expand=True,
        ) for h in headers
    ]
    header_row = ft.Container(
        content=ft.Row(header_cells),
        padding=ft.padding.symmetric(horizontal=14, vertical=8),
        border=ft.border.only(bottom=ft.BorderSide(1, BORDER2)),
    )

    data_rows = []
    for i, row in enumerate(rows):
        cells = []
        for j, cell in enumerate(row):
            if isinstance(cell, ft.Control):
                cells.append(ft.Container(content=cell, expand=True))
            else:
                cells.append(ft.Container(
                    content=ft.Text(str(cell), size=12, color=TEXT),
                    expand=True,
                ))
        data_rows.append(ft.Container(
            content=ft.Row(cells),
            padding=ft.padding.symmetric(horizontal=14, vertical=9),
            bgcolor=SURFACE2 if i % 2 == 0 else SURFACE,
            border=ft.border.only(bottom=ft.BorderSide(0.5, BORDER)),
        ))

    return ft.Container(
        content=ft.Column([header_row, *data_rows], spacing=0),
        bgcolor=SURFACE,
        border_radius=12,
        border=ft.border.all(1, BORDER2),
        clip_behavior=ft.ClipBehavior.HARD_EDGE,
    )
