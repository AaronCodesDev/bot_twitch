#!/usr/bin/env python3
"""
iRacing Dashboard Visual
Interfaz gráfica con Flet para analizar tu rendimiento.

Instalación: pip install flet
Uso: python dashboard.py
"""

import flet as ft
import sqlite3
from pathlib import Path
from datetime import datetime

DB_PATH = Path(__file__).parent / "iracing_data.db"

# ─── Paleta de colores ────────────────────────────────────────────────────────
BG          = "#0D1117"
SIDEBAR_BG  = "#13161C"
CARD_BG     = "#161B22"
ACCENT      = "#F97316"   # Naranja racing
SUCCESS     = "#22C55E"
DANGER      = "#EF4444"
INFO        = "#3B82F6"
TEXT_PRI    = "#E5E7EB"
TEXT_SEC    = "#9CA3AF"
BORDER      = "#30363D"

# ─── Utilidades ──────────────────────────────────────────────────────────────
def fmt_time(seconds):
    """Formatea segundos a mm:ss.fff"""
    if not seconds or seconds <= 0:
        return "--:--.---"
    mins = int(seconds // 60)
    secs = seconds % 60
    return f"{mins}:{secs:06.3f}"

def fmt_speed(mps):
    """m/s → km/h"""
    if mps is None:
        return "---"
    return f"{mps * 3.6:.1f} km/h"


# ─── Componentes base ─────────────────────────────────────────────────────────
def card(content, padding=16, expand=False, height=None):
    return ft.Container(
        content=content,
        bgcolor=CARD_BG,
        border_radius=12,
        padding=ft.padding.all(padding),
        border=ft.border.all(1, BORDER),
        expand=expand,
        height=height,
    )

def stat_card(label, value, icon="", sub=None, sub_positive=True):
    sub_widget = ft.Container()
    if sub is not None:
        color = SUCCESS if sub_positive else DANGER
        arrow = "▲" if sub_positive else "▼"
        sub_widget = ft.Text(f"{arrow} {sub}", size=12, color=color,
                             weight=ft.FontWeight.W_600)
    return card(
        ft.Column([
            ft.Text(f"{icon}  {label}" if icon else label,
                    size=11, color=TEXT_SEC),
            ft.Text(str(value), size=26, weight=ft.FontWeight.BOLD,
                    color=TEXT_PRI),
            sub_widget,
        ], spacing=4),
        expand=True,
    )

def section_title(title, subtitle=""):
    controls = [ft.Text(title, size=22, weight=ft.FontWeight.BOLD,
                        color=TEXT_PRI)]
    if subtitle:
        controls.append(ft.Text(subtitle, size=13, color=TEXT_SEC))
    return ft.Column(controls, spacing=2)

def badge(text, color=ACCENT):
    return ft.Container(
        content=ft.Text(text, size=11, color="white",
                        weight=ft.FontWeight.W_600),
        bgcolor=color,
        border_radius=20,
        padding=ft.padding.symmetric(horizontal=10, vertical=3),
    )

def divider():
    return ft.Divider(height=1, color=BORDER)


# ─── Aplicación principal ─────────────────────────────────────────────────────
class iRacingApp:
    def __init__(self, page: ft.Page):
        self.page = page
        self.conn = sqlite3.connect(str(DB_PATH))
        self.conn.row_factory = sqlite3.Row
        self.content = ft.Column(
            expand=True,
            scroll=ft.ScrollMode.AUTO,
            spacing=0,
        )
        self._setup_page()
        self._build_layout()
        self.show_dashboard()

    # ── Setup ─────────────────────────────────────────────────────────────────
    def _setup_page(self):
        p = self.page
        p.title = "iRacing Tracker"
        p.theme_mode = ft.ThemeMode.DARK
        p.bgcolor = BG
        p.padding = 0
        p.fonts = {"Racing": "https://fonts.googleapis.com/css2?family=Orbitron:wght@700&display=swap"}
        try:
            p.window.width = 1280
            p.window.height = 820
            p.window.min_width = 900
            p.window.min_height = 600
        except Exception:
            pass

    def _build_layout(self):
        NAV = [
            ("🏆", "Dashboard",   self.show_dashboard),
            ("📈", "iRating",     self.show_irating),
            ("📋", "Sesiones",    self.show_sessions),
            ("🚗", "Coches",      self.show_cars),
            ("🏁", "Pistas",      self.show_tracks),
            ("📡", "Telemetría",  self.show_telemetry),
        ]
        self._nav_items = NAV
        self._nav_btns  = []
        self._current   = 0

        # Logo
        logo = ft.Container(
            content=ft.Column([
                ft.Text("🏎️", size=32),
                ft.Text("iRacing", size=16, weight=ft.FontWeight.BOLD,
                        color=ACCENT),
                ft.Text("Tracker", size=11, color=TEXT_SEC),
            ], horizontal_alignment=ft.CrossAxisAlignment.CENTER, spacing=2),
            padding=ft.padding.symmetric(vertical=24),
            alignment=ft.alignment.center,
        )

        nav_col = ft.Column([logo, divider()], spacing=0)

        for i, (icon, label, _) in enumerate(NAV):
            btn = self._make_nav_btn(i, icon, label)
            self._nav_btns.append(btn)
            nav_col.controls.append(btn)

        # Versión en el footer del sidebar
        nav_col.controls.append(ft.Container(expand=True))
        nav_col.controls.append(
            ft.Container(
                content=ft.Text("v2.0", size=10, color=BORDER),
                padding=ft.padding.only(left=20, bottom=16),
            )
        )

        sidebar = ft.Container(
            content=nav_col,
            width=190,
            bgcolor=SIDEBAR_BG,
            border=ft.border.only(right=ft.BorderSide(1, BORDER)),
        )

        main = ft.Container(
            content=self.content,
            expand=True,
            padding=ft.padding.all(28),
        )

        self.page.add(
            ft.Row(
                [sidebar, main],
                expand=True,
                spacing=0,
                vertical_alignment=ft.CrossAxisAlignment.STRETCH,
            )
        )

    def _make_nav_btn(self, i, icon, label):
        selected = i == 0
        return ft.Container(
            content=ft.Row([
                ft.Text(icon, size=17),
                ft.Text(label, size=13, color=TEXT_PRI,
                        weight=ft.FontWeight.W_500),
            ], spacing=10),
            padding=ft.padding.symmetric(horizontal=16, vertical=10),
            border_radius=8,
            bgcolor=f"{ACCENT}25" if selected else "transparent",
            margin=ft.margin.symmetric(horizontal=8, vertical=2),
            on_click=lambda e, idx=i: self._navigate(idx),
            ink=True,
        )

    def _navigate(self, idx):
        for i, btn in enumerate(self._nav_btns):
            btn.bgcolor = f"{ACCENT}25" if i == idx else "transparent"
            btn.update()
        self._current = idx
        self._nav_items[idx][2]()

    def _set_content(self, controls):
        self.content.controls = controls
        self.page.update()

    # ── DB helpers ────────────────────────────────────────────────────────────
    def _q(self, sql, params=()):
        cur = self.conn.cursor()
        cur.execute(sql, params)
        return cur.fetchall()

    def _q1(self, sql, params=()):
        cur = self.conn.cursor()
        cur.execute(sql, params)
        return cur.fetchone()

    # ─────────────────────────────────────────────────────────────────────────
    # DASHBOARD
    # ─────────────────────────────────────────────────────────────────────────
    def show_dashboard(self):
        profile = self._q1("SELECT * FROM driver_profile ORDER BY timestamp DESC LIMIT 1")
        total_sessions = self._q1("SELECT COUNT(*) as cnt FROM sessions")['cnt']
        total_laps     = self._q1("SELECT SUM(total_laps) as s FROM sessions")['s'] or 0
        total_inc      = self._q1("SELECT SUM(total_incidents) as s FROM sessions")['s'] or 0

        races_with_ir = self._q("""
            SELECT irating_change FROM sessions
            WHERE irating_change IS NOT NULL
            ORDER BY session_date DESC LIMIT 20
        """)
        ir_changes = [r['irating_change'] for r in races_with_ir if r['irating_change'] is not None]
        total_ir_chg = sum(ir_changes) if ir_changes else None
        positives    = len([c for c in ir_changes if c > 0])

        name    = profile['display_name'] if profile else "Piloto"
        irating = profile['irating_road']  if profile else "N/A"
        sr      = profile['sr_road']       if profile else "N/A"
        lic     = profile['license_road']  if profile else "N/A"

        # ─ Tarjetas de stats
        top_row = ft.Row([
            stat_card("iRating Road", irating, "📊"),
            stat_card("Safety Rating", sr, "🛡️"),
            stat_card("Licencia", lic, "📄"),
            stat_card("Sesiones", total_sessions, "🏁"),
            stat_card("Vueltas totales", total_laps, "🔄"),
        ], spacing=12)

        # ─ Gráfico iRating
        history = self._q("""
            SELECT session_date, irating_before, irating_after, irating_change
            FROM sessions
            WHERE irating_change IS NOT NULL
            ORDER BY session_date ASC LIMIT 40
        """)

        chart_widget = self._irating_chart(history, height=200)

        # ─ Últimas sesiones
        recent_sessions = self._q("""
            SELECT session_date, track_name, car_name, session_type,
                   irating_change, total_incidents
            FROM sessions ORDER BY session_date DESC LIMIT 8
        """)

        session_rows = []
        for s in recent_sessions:
            ir = s['irating_change']
            color = SUCCESS if (ir or 0) >= 0 else DANGER
            ir_text = ft.Text(f"{ir:+d}" if ir is not None else s['session_type'] or "---",
                              size=12, weight=ft.FontWeight.BOLD,
                              color=color if ir is not None else TEXT_SEC)
            date = (s['session_date'] or '')[:10]
            track = (s['track_name'] or 'Unknown')[:18]
            session_rows.append(
                ft.Container(
                    content=ft.Row([
                        ft.Text(date, size=11, color=TEXT_SEC, width=82),
                        ft.Text(track, size=11, color=TEXT_PRI, expand=True),
                        ft.Text(f"⚠️{s['total_incidents'] or 0}", size=10,
                                color=TEXT_SEC, width=30),
                        ir_text,
                    ], spacing=6),
                    padding=ft.padding.symmetric(vertical=7),
                    border=ft.border.only(bottom=ft.BorderSide(1, BORDER)),
                )
            )

        inc_per_lap = round(total_inc / total_laps, 3) if total_laps else 0

        self._set_content([
            section_title(f"🏎️  Bienvenido, {name}",
                          "Panel de control de tu carrera en iRacing"),
            ft.Container(height=18),
            top_row,
            ft.Container(height=16),
            ft.Row([
                card(ft.Column([
                    ft.Text("📈  Evolución iRating", size=15,
                            weight=ft.FontWeight.BOLD, color=TEXT_PRI),
                    ft.Container(height=8),
                    chart_widget if history else
                    ft.Text("Participa en carreras oficiales para ver\n"
                            "tu evolución de iRating aquí.",
                            color=TEXT_SEC, size=13, text_align=ft.TextAlign.CENTER),
                ]), padding=20, expand=2),
                card(ft.Column([
                    ft.Text("📋  Últimas sesiones", size=15,
                            weight=ft.FontWeight.BOLD, color=TEXT_PRI),
                    ft.Container(height=8),
                    ft.Column(session_rows, spacing=0) if session_rows else
                    ft.Text("Sin sesiones registradas", color=TEXT_SEC),
                ]), padding=20, expand=1),
            ], spacing=16, vertical_alignment=ft.CrossAxisAlignment.START),
            ft.Container(height=14),
            ft.Row([
                stat_card("Win Rate (últimas 20)",
                          f"{positives/len(ir_changes)*100:.1f}%" if ir_changes else "---",
                          "🎯",
                          sub=f"{positives}/{len(ir_changes)}" if ir_changes else None,
                          sub_positive=True),
                stat_card("Cambio iR (últimas 20)",
                          f"{total_ir_chg:+d}" if total_ir_chg is not None else "---",
                          "📉",
                          sub=str(abs(total_ir_chg)) if total_ir_chg else None,
                          sub_positive=(total_ir_chg or 0) >= 0),
                stat_card("Incidentes totales", total_inc, "⚠️"),
                stat_card("Inc / Vuelta", f"{inc_per_lap:.3f}", "🔢"),
            ], spacing=12),
        ])

    # ─────────────────────────────────────────────────────────────────────────
    # IRATING
    # ─────────────────────────────────────────────────────────────────────────
    def show_irating(self):
        history = self._q("""
            SELECT session_date, track_name, car_name,
                   irating_before, irating_after, irating_change,
                   sr_before, sr_after, sr_change,
                   finish_position, total_incidents
            FROM sessions
            WHERE irating_change IS NOT NULL
            ORDER BY session_date DESC LIMIT 50
        """)

        if history:
            changes   = [h['irating_change'] for h in history]
            positives = len([c for c in changes if c > 0])
            negatives = len([c for c in changes if c < 0])
            total_chg = sum(changes)
            best_chg  = max(changes)
            worst_chg = min(changes)
            avg_chg   = total_chg / len(changes) if changes else 0
        else:
            positives = negatives = total_chg = best_chg = worst_chg = 0
            avg_chg = 0

        chart_data = list(reversed(history)) if history else []
        chart = self._irating_chart(chart_data, height=220)

        # Tabla
        rows = []
        for h in history:
            ir = h['irating_change']
            sr = h['sr_change'] or 0
            color = SUCCESS if ir >= 0 else DANGER
            rows.append(ft.DataRow(cells=[
                ft.DataCell(ft.Text((h['session_date'] or '')[:10],
                                   size=12, color=TEXT_SEC)),
                ft.DataCell(ft.Text((h['track_name'] or 'N/A')[:22],
                                   size=12, color=TEXT_PRI)),
                ft.DataCell(ft.Text((h['car_name'] or 'N/A')[:18],
                                   size=11, color=TEXT_SEC)),
                ft.DataCell(ft.Text(str(h['irating_before'] or '---'),
                                   size=12, color=TEXT_PRI)),
                ft.DataCell(ft.Text(f"{ir:+d}" if ir is not None else '---',
                                   size=12, color=color,
                                   weight=ft.FontWeight.BOLD)),
                ft.DataCell(ft.Text(f"{sr:+.2f}" if sr else '---',
                                   size=12,
                                   color=SUCCESS if sr >= 0 else DANGER)),
                ft.DataCell(ft.Text(str(h['total_incidents'] or 0),
                                   size=12, color=TEXT_PRI)),
            ]))

        table = (
            ft.DataTable(
                columns=[
                    ft.DataColumn(ft.Text("Fecha",    size=12, color=TEXT_SEC)),
                    ft.DataColumn(ft.Text("Pista",    size=12, color=TEXT_SEC)),
                    ft.DataColumn(ft.Text("Coche",    size=12, color=TEXT_SEC)),
                    ft.DataColumn(ft.Text("iR",       size=12, color=TEXT_SEC), numeric=True),
                    ft.DataColumn(ft.Text("Δ iR",     size=12, color=TEXT_SEC), numeric=True),
                    ft.DataColumn(ft.Text("Δ SR",     size=12, color=TEXT_SEC), numeric=True),
                    ft.DataColumn(ft.Text("Inc",      size=12, color=TEXT_SEC), numeric=True),
                ],
                rows=rows,
                heading_row_color=BG,
                heading_row_height=38,
                data_row_min_height=34,
                data_row_max_height=38,
                column_spacing=20,
            ) if rows else ft.Text("No hay carreras oficiales registradas todavía.",
                                   color=TEXT_SEC, size=14)
        )

        self._set_content([
            section_title("📈  Historial de iRating",
                          f"Tu evolución en {len(history)} carreras oficiales"),
            ft.Container(height=18),
            ft.Row([
                stat_card("Carreras",   len(history),        "🏁"),
                stat_card("Positivas",  positives,           "🟢"),
                stat_card("Negativas",  negatives,           "🔴"),
                stat_card("Win Rate",   f"{positives/len(history)*100:.1f}%" if history else "---", "🎯"),
                stat_card("Mejor",      f"+{best_chg}" if history else "---", "⬆️"),
                stat_card("Peor",       f"{worst_chg}" if history else "---", "⬇️"),
                stat_card("Promedio",   f"{avg_chg:+.1f}" if history else "---", "〰️"),
            ], spacing=10),
            ft.Container(height=16),
            card(ft.Column([
                ft.Text("Evolución del iRating", size=15,
                        weight=ft.FontWeight.BOLD, color=TEXT_PRI),
                ft.Container(height=12),
                chart if history else
                ft.Container(
                    content=ft.Text("Participa en carreras oficiales para ver\n"
                                    "la evolución de tu iRating aquí.",
                                    color=TEXT_SEC, size=14,
                                    text_align=ft.TextAlign.CENTER),
                    alignment=ft.alignment.center,
                    height=180,
                ),
            ]), padding=20),
            ft.Container(height=16),
            card(ft.Column([
                ft.Text("Detalle por carrera", size=15,
                        weight=ft.FontWeight.BOLD, color=TEXT_PRI),
                ft.Container(height=8),
                table,
            ]), padding=20),
        ])

    # ─────────────────────────────────────────────────────────────────────────
    # SESIONES
    # ─────────────────────────────────────────────────────────────────────────
    def show_sessions(self):
        sessions = self._q("""
            SELECT id, session_date, track_name, track_config, car_name,
                   session_type, total_laps, total_incidents,
                   best_lap_time, avg_lap_time,
                   irating_change, sr_change, finish_position
            FROM sessions ORDER BY session_date DESC LIMIT 60
        """)

        cards = []
        for s in sessions:
            ir = s['irating_change']
            color = SUCCESS if (ir or 0) >= 0 else DANGER
            if ir is not None:
                ir_badge = badge(f"{ir:+d} iR", color)
            else:
                ir_badge = badge(s['session_type'] or "Sesión", "#374151")

            track_str = s['track_name'] or 'Unknown'
            if s['track_config'] and s['track_config'] != s['track_name']:
                track_str += f"  –  {s['track_config']}"

            meta = f"🚗 {(s['car_name'] or 'N/A')[:30]}   •   📅 {(s['session_date'] or '')[:16]}"
            detail = ft.Row([
                ft.Text(f"🏁 {s['total_laps'] or 0} vueltas",
                        size=11, color=TEXT_SEC),
                ft.Text(f"⚠️ {s['total_incidents'] or 0}x",
                        size=11, color=TEXT_SEC),
                ft.Text(f"⏱ {fmt_time(s['best_lap_time'])}",
                        size=11, color=TEXT_SEC),
                ft.Text(f"avg {fmt_time(s['avg_lap_time'])}",
                        size=11, color=TEXT_SEC),
            ], spacing=14)

            c = ft.Container(
                content=ft.Row([
                    ft.Column([
                        ft.Text(track_str, size=14,
                                weight=ft.FontWeight.BOLD, color=TEXT_PRI),
                        ft.Text(meta, size=11, color=TEXT_SEC),
                        ft.Container(height=4),
                        detail,
                    ], expand=True, spacing=3),
                    ft.Column([ir_badge], alignment=ft.MainAxisAlignment.CENTER),
                ], vertical_alignment=ft.CrossAxisAlignment.CENTER),
                bgcolor=CARD_BG,
                border_radius=10,
                padding=ft.padding.all(16),
                border=ft.border.all(1, BORDER),
                on_click=lambda e, sid=s['id']: self._show_session_detail(sid),
                ink=True,
            )
            cards.append(c)

        self._set_content([
            section_title("📋  Sesiones",
                          "Haz clic en cualquier sesión para ver el detalle completo"),
            ft.Container(height=18),
            ft.Column(cards, spacing=8) if cards else
            ft.Text("Sin sesiones registradas", color=TEXT_SEC, size=14),
        ])

    # ─────────────────────────────────────────────────────────────────────────
    # DETALLE DE SESIÓN
    # ─────────────────────────────────────────────────────────────────────────
    def _show_session_detail(self, session_id):
        session = self._q1("SELECT * FROM sessions WHERE id = ?", (session_id,))
        if not session:
            return

        laps = self._q(
            "SELECT * FROM laps WHERE session_id = ? ORDER BY lap_number",
            (session_id,)
        )

        back = ft.TextButton(
            "← Volver a sesiones",
            on_click=lambda e: self._navigate(2),
            style=ft.ButtonStyle(color=ACCENT),
        )

        ir  = session['irating_change']
        sr  = session['sr_change'] or 0

        # Tarjetas superiores
        top = ft.Row([
            stat_card("Pista",  (session['track_name'] or 'N/A')[:22], "🏁"),
            stat_card("Coche",  (session['car_name']  or 'N/A')[:22], "🚗"),
            stat_card("Vueltas", session['total_laps'] or 0, "🔄"),
            stat_card("Incidentes", f"{session['total_incidents'] or 0}x", "⚠️"),
            stat_card("Mejor vuelta", fmt_time(session['best_lap_time']), "⏱"),
            stat_card("Promedio",     fmt_time(session['avg_lap_time']), "〰️"),
        ], spacing=10)

        result_row = ft.Row([
            stat_card("Δ iRating",
                      f"{ir:+d}" if ir is not None else "---",
                      "📊",
                      sub=str(abs(ir)) if ir else None,
                      sub_positive=(ir or 0) >= 0),
            stat_card("Δ Safety Rating",
                      f"{sr:+.2f}" if sr else "---",
                      "🛡️",
                      sub=f"{abs(sr):.2f}" if sr else None,
                      sub_positive=sr >= 0),
            stat_card("Posición final",
                      session['finish_position'] or "---", "🏆"),
            stat_card("Tipo sesión",
                      session['session_type'] or "---", "📌"),
        ], spacing=12) if ir is not None else ft.Container()

        # Gráfico de tiempos de vuelta
        valid_laps = [(l['lap_number'], l['lap_time'])
                      for l in laps
                      if l['lap_time'] and l['lap_time'] > 0]
        lap_chart = ft.Container()
        if len(valid_laps) >= 2:
            pts   = [ft.LineChartDataPoint(x=float(n), y=float(t))
                     for n, t in valid_laps]
            best  = min(t for _, t in valid_laps)
            worst = max(t for _, t in valid_laps)
            margin = max((worst - best) * 0.15, 1.0)
            lap_chart = card(ft.Column([
                ft.Text("⏱  Tiempos de vuelta", size=15,
                        weight=ft.FontWeight.BOLD, color=TEXT_PRI),
                ft.Container(height=10),
                ft.LineChart(
                    data_series=[ft.LineChartData(
                        data_points=pts,
                        stroke_width=2,
                        color=ACCENT,
                        curved=False,
                        stroke_cap_round=True,
                    )],
                    horizontal_grid_lines=ft.ChartGridLines(
                        interval=max((worst - best) / 4, 0.5),
                        color=BORDER, width=1),
                    vertical_grid_lines=ft.ChartGridLines(
                        interval=1, color=BORDER, width=0.5),
                    left_axis=ft.ChartAxis(labels_size=55),
                    bottom_axis=ft.ChartAxis(labels_size=30),
                    min_y=best  - margin,
                    max_y=worst + margin,
                    min_x=float(valid_laps[0][0]),
                    max_x=float(valid_laps[-1][0]),
                    expand=True,
                    height=200,
                    tooltip_bgcolor=CARD_BG,
                ),
            ]), padding=20)

        # Tabla de vueltas
        lap_rows = []
        for l in laps:
            if not l['lap_time'] or l['lap_time'] <= 0:
                continue
            inc = l['incidents_this_lap'] or 0
            lap_rows.append(ft.DataRow(cells=[
                ft.DataCell(ft.Text(str(l['lap_number']),
                                   size=12, color=TEXT_SEC)),
                ft.DataCell(ft.Text(fmt_time(l['lap_time']),
                                   size=13, weight=ft.FontWeight.BOLD,
                                   color=TEXT_PRI)),
                ft.DataCell(ft.Text(str(l['position'] or '---'),
                                   size=12, color=TEXT_PRI)),
                ft.DataCell(ft.Text(
                    f"⚠️ {inc}x" if inc else "—",
                    size=12, color=DANGER if inc else TEXT_SEC,
                )),
                ft.DataCell(ft.Text(
                    f"{l['fuel_remaining']:.1f} L" if l['fuel_remaining'] else "---",
                    size=11, color=TEXT_SEC,
                )),
                ft.DataCell(ft.Text(
                    "🔧 PIT" if l['pit_stop'] else "",
                    size=11, color=ACCENT,
                )),
            ]))

        laps_table = (
            ft.DataTable(
                columns=[
                    ft.DataColumn(ft.Text("Vuelta", size=12, color=TEXT_SEC), numeric=True),
                    ft.DataColumn(ft.Text("Tiempo", size=12, color=TEXT_SEC)),
                    ft.DataColumn(ft.Text("Pos.",   size=12, color=TEXT_SEC), numeric=True),
                    ft.DataColumn(ft.Text("Inc.",   size=12, color=TEXT_SEC), numeric=True),
                    ft.DataColumn(ft.Text("Fuel",   size=12, color=TEXT_SEC)),
                    ft.DataColumn(ft.Text("Pit",    size=12, color=TEXT_SEC)),
                ],
                rows=lap_rows,
                heading_row_color=BG,
                heading_row_height=36,
                data_row_min_height=32,
                data_row_max_height=36,
                column_spacing=20,
            ) if lap_rows else
            ft.Text("Sin datos de vueltas", color=TEXT_SEC, size=13)
        )

        self._set_content([
            back,
            ft.Container(height=6),
            section_title(
                f"📋  {session['track_name'] or 'Sesión'}",
                f"{session['car_name'] or ''}   •   "
                f"{(session['session_date'] or '')[:16]}   •   "
                f"{session['session_type'] or 'Sesión'}"
            ),
            ft.Container(height=16),
            top,
            ft.Container(height=10),
            result_row,
            ft.Container(height=14),
            lap_chart,
            ft.Container(height=14) if valid_laps else ft.Container(),
            card(ft.Column([
                ft.Text("📝  Detalle de vueltas", size=15,
                        weight=ft.FontWeight.BOLD, color=TEXT_PRI),
                ft.Container(height=8),
                laps_table,
            ]), padding=20),
        ])

    # ─────────────────────────────────────────────────────────────────────────
    # COCHES
    # ─────────────────────────────────────────────────────────────────────────
    def show_cars(self):
        cars = self._q("""
            SELECT
                car_name,
                COUNT(*)  as races,
                SUM(CASE WHEN session_type='Race' AND irating_change > 0 THEN 1 ELSE 0 END) as wins_ir,
                SUM(CASE WHEN session_type='Race' AND irating_change < 0 THEN 1 ELSE 0 END) as losses_ir,
                AVG(CASE WHEN session_type='Race' THEN irating_change END) as avg_ir,
                SUM(total_incidents) as total_inc,
                SUM(total_laps) as total_laps,
                MIN(best_lap_time) as best_lap
            FROM sessions
            WHERE car_name IS NOT NULL
            GROUP BY car_name
            ORDER BY races DESC
        """)

        car_cards = []
        for c in cars:
            total  = (c['wins_ir'] or 0) + (c['losses_ir'] or 0)
            wr     = (c['wins_ir'] or 0) / total * 100 if total > 0 else None
            avg_ir = c['avg_ir'] or 0
            ipl    = (c['total_inc'] or 0) / max(c['total_laps'] or 1, 1)
            color  = SUCCESS if avg_ir >= 0 else DANGER

            car_cards.append(card(ft.Column([
                ft.Row([
                    ft.Text(f"🚗  {c['car_name'] or 'N/A'}",
                            size=16, weight=ft.FontWeight.BOLD, color=TEXT_PRI,
                            expand=True),
                    badge(f"{avg_ir:+.1f} iR/carrera" if c['wins_ir'] or c['losses_ir'] else "Sin carreras oficiales", color),
                ]),
                ft.Container(height=14),
                ft.Row([
                    ft.Column([ft.Text("Sesiones",   size=11, color=TEXT_SEC),
                               ft.Text(str(c['races']), size=24,
                                       weight=ft.FontWeight.BOLD, color=TEXT_PRI)],
                              horizontal_alignment=ft.CrossAxisAlignment.CENTER),
                    ft.VerticalDivider(color=BORDER),
                    ft.Column([ft.Text("Win Rate",  size=11, color=TEXT_SEC),
                               ft.Text(f"{wr:.1f}%" if wr is not None else "---",
                                       size=24, weight=ft.FontWeight.BOLD,
                                       color=SUCCESS if (wr or 0) >= 50 else TEXT_PRI)],
                              horizontal_alignment=ft.CrossAxisAlignment.CENTER),
                    ft.VerticalDivider(color=BORDER),
                    ft.Column([ft.Text("Inc/Vuelta", size=11, color=TEXT_SEC),
                               ft.Text(f"{ipl:.3f}", size=24,
                                       weight=ft.FontWeight.BOLD, color=TEXT_PRI)],
                              horizontal_alignment=ft.CrossAxisAlignment.CENTER),
                    ft.VerticalDivider(color=BORDER),
                    ft.Column([ft.Text("Mejor vuelta", size=11, color=TEXT_SEC),
                               ft.Text(fmt_time(c['best_lap']), size=18,
                                       weight=ft.FontWeight.BOLD, color=ACCENT)],
                              horizontal_alignment=ft.CrossAxisAlignment.CENTER),
                ], spacing=28, alignment=ft.MainAxisAlignment.SPACE_EVENLY),
            ], spacing=0), padding=20))

        self._set_content([
            section_title("🚗  Rendimiento por Coche",
                          "Estadísticas de tu rendimiento en cada vehículo"),
            ft.Container(height=18),
            ft.Column(car_cards, spacing=12) if car_cards else
            ft.Text("Sin datos de coches todavía", color=TEXT_SEC, size=14),
        ])

    # ─────────────────────────────────────────────────────────────────────────
    # PISTAS
    # ─────────────────────────────────────────────────────────────────────────
    def show_tracks(self):
        tracks = self._q("""
            SELECT
                track_name,
                COUNT(DISTINCT id) as sessions,
                SUM(total_laps) as total_laps,
                MIN(best_lap_time) as best_lap,
                SUM(CASE WHEN irating_change > 0 THEN 1 ELSE 0 END) as pos,
                SUM(CASE WHEN irating_change < 0 THEN 1 ELSE 0 END) as neg,
                AVG(irating_change) as avg_ir,
                SUM(total_incidents) as total_inc
            FROM sessions
            WHERE track_name IS NOT NULL
            GROUP BY track_name
            ORDER BY sessions DESC
        """)

        rows = []
        for t in tracks:
            total  = (t['pos'] or 0) + (t['neg'] or 0)
            wr     = (t['pos'] or 0) / total * 100 if total > 0 else None
            avg_ir = t['avg_ir'] or 0
            rows.append(ft.DataRow(cells=[
                ft.DataCell(ft.Text(t['track_name'] or '---',
                                   size=12, color=TEXT_PRI)),
                ft.DataCell(ft.Text(str(t['sessions']), size=12, color=TEXT_PRI)),
                ft.DataCell(ft.Text(str(t['total_laps'] or 0),
                                   size=12, color=TEXT_PRI)),
                ft.DataCell(ft.Text(fmt_time(t['best_lap']),
                                   size=12, color=ACCENT,
                                   weight=ft.FontWeight.BOLD)),
                ft.DataCell(ft.Text(
                    f"{wr:.1f}%" if wr is not None else "---",
                    size=12,
                    color=SUCCESS if (wr or 0) >= 50 else
                          (DANGER if wr is not None else TEXT_SEC),
                )),
                ft.DataCell(ft.Text(
                    f"{avg_ir:+.1f}" if avg_ir else "---",
                    size=12,
                    color=SUCCESS if avg_ir >= 0 else DANGER,
                    weight=ft.FontWeight.BOLD,
                )),
                ft.DataCell(ft.Text(str(t['total_inc'] or 0),
                                   size=12, color=TEXT_PRI)),
            ]))

        table = (
            ft.DataTable(
                columns=[
                    ft.DataColumn(ft.Text("Pista",       size=12, color=TEXT_SEC)),
                    ft.DataColumn(ft.Text("Sesiones",    size=12, color=TEXT_SEC), numeric=True),
                    ft.DataColumn(ft.Text("Vueltas",     size=12, color=TEXT_SEC), numeric=True),
                    ft.DataColumn(ft.Text("Mejor vuelta",size=12, color=TEXT_SEC)),
                    ft.DataColumn(ft.Text("Win Rate",    size=12, color=TEXT_SEC), numeric=True),
                    ft.DataColumn(ft.Text("Avg iR",      size=12, color=TEXT_SEC), numeric=True),
                    ft.DataColumn(ft.Text("Inc",         size=12, color=TEXT_SEC), numeric=True),
                ],
                rows=rows,
                heading_row_color=BG,
                heading_row_height=38,
                data_row_min_height=34,
                data_row_max_height=38,
                column_spacing=20,
            ) if rows else ft.Text("Sin datos de pistas", color=TEXT_SEC, size=14)
        )

        self._set_content([
            section_title("🏁  Estadísticas por Pista",
                          "Tu rendimiento en cada circuito"),
            ft.Container(height=18),
            card(ft.Column([
                ft.Container(content=table, expand=True),
            ]), padding=20),
        ])

    # ─────────────────────────────────────────────────────────────────────────
    # TELEMETRÍA
    # ─────────────────────────────────────────────────────────────────────────
    def show_telemetry(self):
        # Sesiones con telemetría
        sessions_with_tel = self._q("""
            SELECT DISTINCT s.id, s.session_date, s.track_name, s.car_name,
                   COUNT(t.id) as tel_rows
            FROM sessions s
            JOIN telemetry t ON t.session_id = s.id
            GROUP BY s.id
            ORDER BY s.session_date DESC
        """)

        if not sessions_with_tel:
            self._set_content([
                section_title("📡  Telemetría", "Datos en tiempo real de tus sesiones"),
                ft.Container(height=30),
                ft.Container(
                    content=ft.Column([
                        ft.Text("📡", size=48),
                        ft.Text("Sin datos de telemetría todavía",
                                size=18, color=TEXT_PRI,
                                weight=ft.FontWeight.BOLD),
                        ft.Text("Ejecuta el logger mientras corres para capturar\n"
                                "datos de throttle, freno, velocidad y más.",
                                size=13, color=TEXT_SEC,
                                text_align=ft.TextAlign.CENTER),
                    ], horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                       spacing=8),
                    alignment=ft.alignment.center,
                    height=300,
                ),
            ])
            return

        # Mostrar la primera sesión por defecto
        self._show_telemetry_session(sessions_with_tel[0]['id'], sessions_with_tel)

    def _show_telemetry_session(self, session_id, session_list):
        session = self._q1("SELECT * FROM sessions WHERE id = ?", (session_id,))

        # Telemetría de una vuelta representativa (la más larga)
        laps_in_tel = self._q("""
            SELECT lap_number, COUNT(*) as pts
            FROM telemetry WHERE session_id = ?
            GROUP BY lap_number
            ORDER BY pts DESC LIMIT 1
        """, (session_id,))

        selected_lap = laps_in_tel[0]['lap_number'] if laps_in_tel else 0

        tel = self._q("""
            SELECT timestamp, speed, throttle, brake, rpm, gear,
                   lat_accel, long_accel, track_position
            FROM telemetry
            WHERE session_id = ? AND lap_number = ?
            ORDER BY timestamp ASC
        """, (session_id, selected_lap))

        charts_col = []

        if tel:
            # Normalizar timestamps a segundos desde inicio
            t0 = tel[0]['timestamp']
            times  = [r['timestamp'] - t0 for r in tel]
            speeds = [r['speed'] * 3.6 for r in tel]         # km/h
            throttles = [r['throttle'] * 100 for r in tel]   # 0-100
            brakes    = [r['brake'] for r in tel]             # ya en %
            rpms      = [r['rpm'] for r in tel]

            max_t = max(times) if times else 1

            def make_chart(label, color, data_y, min_y=0, max_y=None, h=130):
                if max_y is None:
                    max_y = max(data_y) * 1.05 if data_y else 1
                step = max(len(data_y) // 60, 1)
                pts  = [ft.LineChartDataPoint(x=times[i], y=data_y[i])
                        for i in range(0, len(data_y), step)]
                return card(ft.Column([
                    ft.Text(label, size=13, weight=ft.FontWeight.W_600,
                            color=color),
                    ft.Container(height=6),
                    ft.LineChart(
                        data_series=[ft.LineChartData(
                            data_points=pts,
                            stroke_width=1.5,
                            color=color,
                            curved=False,
                        )],
                        horizontal_grid_lines=ft.ChartGridLines(
                            interval=(max_y - min_y) / 4, color=BORDER, width=0.8),
                        vertical_grid_lines=ft.ChartGridLines(
                            interval=max_t / 6, color=BORDER, width=0.5),
                        left_axis=ft.ChartAxis(labels_size=40),
                        bottom_axis=ft.ChartAxis(labels_size=28),
                        min_y=min_y, max_y=max_y,
                        min_x=0.0,  max_x=max_t,
                        expand=True, height=h,
                        tooltip_bgcolor=CARD_BG,
                    ),
                ]), padding=16)

            max_speed = max(speeds) * 1.05 if speeds else 300
            charts_col = [
                make_chart(f"🚀  Velocidad  (km/h)  —  máx. {max(speeds):.1f} km/h",
                           INFO, speeds, 0, max_speed, 160),
                ft.Container(height=10),
                ft.Row([
                    ft.Container(content=make_chart("🟢  Throttle (%)", SUCCESS, throttles, 0, 105, 130), expand=True),
                    ft.Container(content=make_chart("🔴  Freno (%)",    DANGER,  brakes,    0, 105, 130), expand=True),
                ], spacing=12),
                ft.Container(height=10),
                make_chart(f"⚙️  RPM",  "#A78BFA", rpms, 0, max(rpms)*1.05 if rpms else 9000, 130),
            ]

        # Selector de sesión
        session_options = [
            ft.dropdown.Option(
                key=str(s['id']),
                text=f"{(s['session_date'] or '')[:10]}  –  {s['track_name'] or 'N/A'}  ({s['tel_rows']} pts)"
            )
            for s in session_list
        ]
        dd = ft.Dropdown(
            options=session_options,
            value=str(session_id),
            bgcolor=CARD_BG,
            border_color=BORDER,
            color=TEXT_PRI,
            width=480,
            on_change=lambda e: self._show_telemetry_session(int(e.control.value), session_list),
        )

        self._set_content([
            section_title("📡  Telemetría",
                          f"Vuelta {selected_lap}  —  {session['track_name'] or ''}  |  {session['car_name'] or ''}"),
            ft.Container(height=16),
            ft.Row([ft.Text("Sesión:", size=13, color=TEXT_SEC), dd], spacing=10,
                   vertical_alignment=ft.CrossAxisAlignment.CENTER),
            ft.Container(height=16),
            *charts_col,
        ])

    # ─────────────────────────────────────────────────────────────────────────
    # HELPERS COMPARTIDOS
    # ─────────────────────────────────────────────────────────────────────────
    def _irating_chart(self, history, height=200):
        """Gráfico de línea para iRating."""
        points = []
        for i, row in enumerate(history):
            ir = row['irating_after'] or row['irating_before']
            if ir:
                points.append(ft.LineChartDataPoint(x=float(i), y=float(ir)))

        if len(points) < 2:
            return ft.Container(
                content=ft.Text("Necesitas al menos 2 carreras para ver la gráfica.",
                                color=TEXT_SEC, size=13,
                                text_align=ft.TextAlign.CENTER),
                alignment=ft.alignment.center,
                height=height,
            )

        min_ir = min(p.y for p in points) - 50
        max_ir = max(p.y for p in points) + 50

        return ft.LineChart(
            data_series=[ft.LineChartData(
                data_points=points,
                stroke_width=2.5,
                color=ACCENT,
                curved=True,
                stroke_cap_round=True,
                below_line_gradient=ft.LinearGradient(
                    begin=ft.alignment.top_center,
                    end=ft.alignment.bottom_center,
                    colors=[f"{ACCENT}55", f"{ACCENT}00"],
                ),
            )],
            horizontal_grid_lines=ft.ChartGridLines(
                interval=max(100, (max_ir - min_ir) / 5),
                color=BORDER, width=1),
            vertical_grid_lines=ft.ChartGridLines(
                interval=max(1, len(points) / 8),
                color=BORDER, width=0.8),
            left_axis=ft.ChartAxis(labels_size=48),
            bottom_axis=ft.ChartAxis(labels_size=28),
            min_y=min_ir,
            max_y=max_ir,
            min_x=0.0,
            max_x=float(len(points) - 1),
            expand=True,
            height=height,
            tooltip_bgcolor=CARD_BG,
        )


# ─── Entry point ──────────────────────────────────────────────────────────────
def main(page: ft.Page):
    iRacingApp(page)


if __name__ == "__main__":
    ft.app(target=main)
