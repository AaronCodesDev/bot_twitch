# ui/views/tracker_view.py
# Vista iRacing Tracker — FanTan Hub

import flet as ft
import sqlite3
import os
import sys
import threading
from ui.colors import *
from ui.components import *


BASE = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
TRACKER_DB   = os.path.join(BASE, "iracing_tracker", "iracing_data.db")
TRACKER_BASE = os.path.join(BASE, "iracing_tracker")


def _q(query: str, default=None):
    try:
        if not os.path.exists(TRACKER_DB):
            return default
        conn = sqlite3.connect(TRACKER_DB)
        conn.row_factory = sqlite3.Row
        r = conn.cursor().execute(query).fetchone()
        conn.close()
        return r[0] if r and r[0] is not None else default
    except Exception:
        return default


def _qa(query: str):
    try:
        if not os.path.exists(TRACKER_DB):
            return []
        conn = sqlite3.connect(TRACKER_DB)
        conn.row_factory = sqlite3.Row
        rows = conn.cursor().execute(query).fetchall()
        conn.close()
        return [dict(r) for r in rows]
    except Exception:
        return []


def _fmt_time(seconds) -> str:
    if not seconds or seconds <= 0:
        return "--:--.---"
    try:
        s = float(seconds)
        mins = int(s // 60)
        secs = s % 60
        return f"{mins}:{secs:06.3f}"
    except Exception:
        return "--:--.---"


class TrackerView:
    def __init__(self, state: dict, page: ft.Page):
        self.state = state
        self.page = page
        self._telemetry_visible = False

    # ─── Build ────────────────────────────────────────────────────────────────
    def build(self) -> ft.Control:
        # Estadísticas generales
        total_sessions = _q("SELECT COUNT(*) FROM sessions", 0) or 0
        total_laps     = _q("SELECT COUNT(*) FROM laps", 0) or 0
        best_lap       = _q("SELECT MIN(lap_time) FROM laps WHERE lap_time > 10", None)
        best_irating   = _q("SELECT MAX(irating_before) FROM sessions WHERE irating_before > 0", None)
        best_sr        = _q("SELECT MAX(sr_before) FROM sessions WHERE sr_before > 0", None)
        avg_incidents  = _q("SELECT AVG(total_incidents) FROM sessions WHERE total_incidents IS NOT NULL", None)
        total_incidents= _q("SELECT SUM(total_incidents) FROM sessions", 0) or 0
        wins           = _q("SELECT COUNT(*) FROM sessions WHERE finish_position = 1", 0) or 0
        top3           = _q("SELECT COUNT(*) FROM sessions WHERE finish_position <= 3 AND finish_position > 0", 0) or 0

        logger_running = self.state.get("tracker_running", False)

        header = module_header(
            "🏎️", "iRacing Tracker",
            subtitle="Telemetría & estadísticas en tiempo real",
            accent=ORANGE,
            actions=[
                self._logger_toggle_btn(logger_running),
                secondary_button("Importar historial", ft.Icons.UPLOAD_FILE_OUTLINED,
                                 ORANGE, on_click=self._import_history),
            ],
        )

        def _cs(icon, label, value, accent):
            return ft.Container(
                content=ft.Row([
                    ft.Text(icon, size=14),
                    ft.Column([
                        ft.Text(value, size=14, weight=ft.FontWeight.W_800, color=TEXT),
                        ft.Text(label, size=9, color=MUTED),
                    ], spacing=0, expand=True),
                ], spacing=7),
                bgcolor=with_alpha(accent, 0.06),
                border_radius=9,
                border=ft.border.only(left=ft.BorderSide(2, accent)),
                padding=ft.padding.symmetric(horizontal=11, vertical=7),
                expand=True,
            )

        sr_str = f"{best_sr:.2f}" if best_sr else "---"

        stats_row = ft.Row([
            _cs("🏁", "Sesiones",     str(total_sessions),                          ORANGE),
            _cs("🔄", "Vueltas",      str(total_laps),                              ORANGE),
            _cs("📈", "iRating máx.", str(best_irating) if best_irating else "---", GREEN),
            _cs("🛡️", "Safety R.",    sr_str,                                       GREEN),
        ], spacing=8)

        stats_row2 = ft.Row([
            _cs("⏱️", "Mejor vuelta", _fmt_time(best_lap),                                                                                CYAN),
            _cs("🥇", "Victorias",   str(wins),                                                                                           WARNING),
            _cs("🏅", "Top 3",       str(top3),                                                                                           GREEN),
            _cs("⚠️", "Incidentes",  f"{total_incidents}  (x̄ {avg_incidents:.1f})" if avg_incidents else str(total_incidents),           DANGER),
        ], spacing=8)

        # Tabs
        tabs = ft.Tabs(
            selected_index=0,
            animation_duration=250,
            tab_alignment=ft.TabAlignment.START,
            indicator_color=ORANGE,
            label_color=ORANGE,
            unselected_label_color=MUTED,
            tabs=[
                ft.Tab(text="Sesiones", icon=ft.Icons.LIST_ALT_OUTLINED,
                       content=self._build_sessions_tab()),
                ft.Tab(text="Análisis", icon=ft.Icons.BAR_CHART_OUTLINED,
                       content=self._build_analysis_tab()),
                ft.Tab(text="Perfil", icon=ft.Icons.PERSON_OUTLINE,
                       content=self._build_profile_tab()),
                ft.Tab(text="Telemetría Live", icon=ft.Icons.SENSORS_OUTLINED,
                       content=self._build_live_tab()),
            ],
            expand=True,
        )

        return ft.Column([
            header,
            ft.Container(height=12),
            stats_row,
            ft.Container(height=6),
            stats_row2,
            ft.Container(height=12),
            ft.Container(content=tabs, expand=True),
        ], spacing=0, expand=True)

    # ─── Sessions tab ─────────────────────────────────────────────────────────
    def _build_sessions_tab(self) -> ft.Container:
        sessions = _qa("""
            SELECT track_name, track_config, car_name, session_type,
                   finish_position, total_laps, total_incidents,
                   best_lap_time, irating_before, irating_after,
                   irating_change, sr_before, sr_after, sr_change, session_date
            FROM sessions
            ORDER BY session_date DESC
            LIMIT 30
        """)

        rows = []
        for s in sessions:
            pos = s.get("finish_position")
            ir_change = s.get("irating_change") or 0
            pos_color = (WARNING if pos == 1 else
                         GREEN if pos and pos <= 3 else
                         DANGER if pos and pos > 40 else MUTED)
            pos_label = "DQ" if pos and pos > 40 else (str(pos) if pos else "?")

            rows.append([
                ft.Container(
                    content=ft.Text(pos_label, size=12, color=pos_color,
                                    weight=ft.FontWeight.W_700,
                                    text_align=ft.TextAlign.CENTER),
                    width=32, height=28,
                    bgcolor=with_alpha(pos_color, 0.12),
                    border_radius=6,
                    alignment=ft.Alignment(0, 0),
                    expand=True,
                ),
                ft.Column([
                    ft.Text(s.get("track_name", "?"), size=12, color=TEXT,
                            weight=ft.FontWeight.W_500),
                    ft.Text(s.get("car_name", "")[:25], size=10, color=MUTED),
                ], spacing=1, expand=True),
                s.get("session_type", "---"),
                _fmt_time(s.get("best_lap_time")),
                f"{s.get('total_incidents', 0)}x",
                ft.Container(
                    content=ft.Text(
                        f"{'+'if ir_change >= 0 else ''}{ir_change}",
                        size=12,
                        color=GREEN if ir_change >= 0 else DANGER,
                        weight=ft.FontWeight.W_600,
                    ),
                    expand=True,
                ),
            ])

        return ft.Container(
            content=ft.Column([
                ft.Container(height=12),
                section_title(f"Historial de sesiones ({len(sessions)})", accent=ORANGE),
                ft.Container(height=8),
                ft.Container(
                    content=simple_table(
                        ["Pos.", "Pista / Coche", "Tipo", "Mejor vuelta", "Inc.", "iRating Δ"],
                        rows if rows else [["—", "Sin sesiones registradas", "—", "—", "—", "—"]],
                        accent=ORANGE,
                    ),
                    expand=True,
                ),
            ], spacing=0, scroll=ft.ScrollMode.AUTO, expand=True),
            expand=True,
        )

    # ─── Analysis tab ─────────────────────────────────────────────────────────
    def _build_analysis_tab(self) -> ft.Container:
        # iRating evolution
        ir_data = _qa("""
            SELECT irating_before, irating_after, session_date, track_name
            FROM sessions
            WHERE irating_before IS NOT NULL AND irating_before > 0
            ORDER BY session_date DESC
            LIMIT 10
        """)

        # Best laps by track
        best_by_track = _qa("""
            SELECT s.track_name, MIN(l.lap_time) as best_lap, COUNT(l.id) as total_laps
            FROM laps l JOIN sessions s ON l.session_id = s.id
            WHERE l.lap_time > 10
            GROUP BY s.track_name
            ORDER BY best_lap ASC
            LIMIT 10
        """)

        # Consistency analysis
        consistency = _qa("""
            SELECT s.track_name,
                   MAX(l.lap_time) - MIN(l.lap_time) as delta,
                   AVG(l.lap_time) as avg_time,
                   COUNT(l.id) as laps
            FROM laps l JOIN sessions s ON l.session_id = s.id
            WHERE l.lap_time > 10 AND l.pit_stop = 0
            GROUP BY s.track_name
            HAVING laps >= 3
            ORDER BY delta ASC
            LIMIT 8
        """)

        # iRating chart (simulated visual)
        ir_chart_controls = []
        if ir_data:
            max_ir = max((d.get("irating_before") or 0) for d in ir_data)
            min_ir = min((d.get("irating_before") or 0) for d in ir_data if d.get("irating_before"))
            ir_range = max(max_ir - min_ir, 1)
            chart_h = 80

            bars = []
            for d in reversed(ir_data):
                ir = d.get("irating_before") or 0
                pct = (ir - min_ir) / ir_range
                bars.append(
                    ft.Container(
                        content=ft.Column([
                            ft.Container(expand=True),
                            ft.Tooltip(
                                message=f"{d.get('track_name','')}\niRating: {ir}",
                                content=ft.Container(
                                    width=18,
                                    height=max(4, int(pct * chart_h)),
                                    bgcolor=ORANGE,
                                    border_radius=ft.border_radius.only(top_left=4, top_right=4),
                                ),
                            ),
                        ], spacing=0),
                        expand=True,
                        height=chart_h + 10,
                    )
                )

            ir_chart_controls = [
                ft.Column([
                    ft.Text("Evolución iRating (últimas sesiones)", size=11, color=MUTED,
                            weight=ft.FontWeight.W_500),
                    ft.Container(height=8),
                    ft.Row(bars, spacing=4, expand=True,
                           alignment=ft.MainAxisAlignment.CENTER),
                    ft.Row([
                        ft.Text(f"Min: {min_ir}", size=10, color=MUTED),
                        ft.Container(expand=True),
                        ft.Text(f"Max: {max_ir}", size=10, color=ORANGE, weight=ft.FontWeight.W_600),
                    ]),
                ], spacing=4)
            ]

        # Best laps table
        lap_rows = []
        for b in best_by_track:
            lap_rows.append([
                b.get("track_name", "---")[:30],
                _fmt_time(b.get("best_lap")),
                f"{b.get('total_laps', 0)} vueltas",
            ])

        # Consistency table
        cons_rows = []
        for c in consistency:
            delta = c.get("delta") or 0
            cons_rows.append([
                c.get("track_name", "---")[:25],
                f"±{_fmt_time(delta)}",
                _fmt_time(c.get("avg_time")),
                ft.Container(
                    content=ft.Text(
                        "✓ Buena" if delta < 2 else ("⚠ Regular" if delta < 5 else "✗ Inconsistente"),
                        size=11,
                        color=GREEN if delta < 2 else (WARNING if delta < 5 else DANGER),
                    ),
                    expand=True,
                ),
            ])

        empty_analysis = ft.Container(
            content=ft.Column([
                ft.Text("📊", size=48, text_align=ft.TextAlign.CENTER),
                ft.Text("Sin datos suficientes para el análisis", size=14, color=MUTED,
                        text_align=ft.TextAlign.CENTER),
                ft.Text("Corre algunas sesiones y vuelve aquí", size=12, color=MUTED2,
                        text_align=ft.TextAlign.CENTER),
            ], horizontal_alignment=ft.CrossAxisAlignment.CENTER,
               alignment=ft.MainAxisAlignment.CENTER),
            alignment=ft.Alignment(0, 0),
            expand=True,
        ) if not ir_data and not best_by_track else None

        content = []
        if empty_analysis:
            content.append(empty_analysis)
        else:
            if ir_chart_controls:
                content.append(
                    card(ft.Column(ir_chart_controls, spacing=0), expand=True, bgcolor=SURFACE)
                )
            content.append(ft.Container(height=14))
            content.append(
                ft.Row([
                    ft.Column([
                        section_title("Mejores vueltas por circuito", accent=ORANGE),
                        ft.Container(height=8),
                        simple_table(
                            ["Circuito", "Mejor vuelta", "Vueltas"],
                            lap_rows if lap_rows else [["Sin datos", "---", "---"]],
                            accent=ORANGE,
                        ),
                    ], spacing=0, expand=True),
                    ft.Container(width=14),
                    ft.Column([
                        section_title("Consistencia", accent=CYAN),
                        ft.Container(height=8),
                        simple_table(
                            ["Circuito", "Variación", "Media", "Estado"],
                            cons_rows if cons_rows else [["Sin datos", "---", "---", "---"]],
                            accent=CYAN,
                        ),
                    ], spacing=0, expand=True),
                ], spacing=0, expand=True)
            )

        return ft.Container(
            content=ft.Column(
                [ft.Container(height=12)] + content,
                spacing=0, scroll=ft.ScrollMode.AUTO, expand=True,
            ),
            expand=True,
        )

    # ─── Profile tab ──────────────────────────────────────────────────────────
    def _build_profile_tab(self) -> ft.Container:
        profile = _qa("""
            SELECT display_name, irating_road, sr_road, license_road,
                   laps_road, wins_road, starts_road, timestamp
            FROM driver_profile
            ORDER BY timestamp DESC
            LIMIT 1
        """)

        irating_history = _qa("""
            SELECT irating_road, timestamp
            FROM driver_profile
            WHERE irating_road > 0
            ORDER BY timestamp DESC
            LIMIT 20
        """)

        if not profile:
            return ft.Container(
                content=ft.Column([
                    ft.Container(height=30),
                    ft.Text("🏎️", size=56, text_align=ft.TextAlign.CENTER),
                    ft.Text("Perfil de piloto no disponible", size=16, color=MUTED,
                            text_align=ft.TextAlign.CENTER),
                    ft.Text("Configura las credenciales de iRacing en el .env del tracker",
                            size=12, color=MUTED2, text_align=ft.TextAlign.CENTER),
                    ft.Container(height=16),
                    badge("Ejecuta iracing_logger.py para capturar tu perfil", ORANGE),
                ], horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                   alignment=ft.MainAxisAlignment.CENTER, spacing=12),
                alignment=ft.Alignment(0, 0),
                expand=True,
            )

        p = profile[0]
        pilot_name = p.get("display_name", "Piloto")
        irating = p.get("irating_road", 0) or 0
        sr       = p.get("sr_road", 0) or 0
        license_ = p.get("license_road", "R") or "R"
        laps     = p.get("laps_road", 0) or 0
        wins     = p.get("wins_road", 0) or 0
        starts   = p.get("starts_road", 0) or 0
        win_rate = f"{(wins/max(starts,1)*100):.1f}%" if starts > 0 else "0%"

        # iRating trend
        ir_trend = 0
        if len(irating_history) >= 2:
            ir_trend = (irating_history[0].get("irating_road") or 0) - (irating_history[-1].get("irating_road") or 0)

        # License badge color
        lic_colors = {"R": MUTED2, "D": WARNING, "C": ORANGE, "B": INFO, "A": GREEN, "Pro": PURPLE}
        lic_color = lic_colors.get(license_, MUTED2)

        pilot_card = ft.Container(
            content=ft.Row([
                ft.Container(
                    content=ft.Column([
                        ft.Text("🏎️", size=36, text_align=ft.TextAlign.CENTER),
                        ft.Container(
                            content=ft.Text(license_, size=14, color="white",
                                            weight=ft.FontWeight.W_900),
                            bgcolor=lic_color, border_radius=8,
                            padding=ft.padding.symmetric(horizontal=12, vertical=4),
                        ),
                    ], horizontal_alignment=ft.CrossAxisAlignment.CENTER, spacing=8),
                    width=100,
                ),
                ft.Column([
                    ft.Text(pilot_name, size=20, weight=ft.FontWeight.W_700, color=TEXT),
                    ft.Row([
                        ft.Text(f"iRating: ", size=12, color=MUTED),
                        ft.Text(str(irating), size=18, color=ORANGE,
                                weight=ft.FontWeight.W_700),
                        ft.Text(
                            f"  ({'+'if ir_trend >= 0 else ''}{ir_trend})",
                            size=12,
                            color=GREEN if ir_trend >= 0 else DANGER,
                        ),
                    ], spacing=4),
                    ft.Row([
                        ft.Text(f"Safety Rating: ", size=12, color=MUTED),
                        ft.Text(f"{sr:.2f}", size=16, color=GREEN,
                                weight=ft.FontWeight.W_600),
                    ], spacing=4),
                ], spacing=6, expand=True),
            ], spacing=20),
            bgcolor=SURFACE2,
            border_radius=14,
            padding=ft.padding.symmetric(horizontal=20, vertical=18),
            border=ft.border.all(1, with_alpha(ORANGE, 0.25)),
        )

        career_stats = ft.Row([
            self._big_stat("Inicios", str(starts), ORANGE),
            self._big_stat("Victorias", str(wins), WARNING),
            self._big_stat("Win Rate", win_rate, GREEN),
            self._big_stat("Vueltas totales", str(laps), CYAN),
        ], spacing=12, expand=True)

        return ft.Container(
            content=ft.Column([
                ft.Container(height=12),
                pilot_card,
                ft.Container(height=14),
                section_title("Estadísticas de carrera", accent=ORANGE),
                ft.Container(height=10),
                career_stats,
            ], spacing=0, scroll=ft.ScrollMode.AUTO, expand=True),
            expand=True,
        )

    def _big_stat(self, label: str, value: str, color: str) -> ft.Container:
        return ft.Container(
            content=ft.Column([
                ft.Text(value, size=26, weight=ft.FontWeight.W_700, color=color),
                ft.Text(label, size=11, color=MUTED),
            ], spacing=4, horizontal_alignment=ft.CrossAxisAlignment.CENTER),
            bgcolor=SURFACE,
            border_radius=12,
            border=ft.border.all(1, with_alpha(color, 0.2)),
            padding=ft.padding.symmetric(horizontal=16, vertical=14),
            expand=True,
        )

    # ─── Live telemetry tab ───────────────────────────────────────────────────
    def _build_live_tab(self) -> ft.Container:
        speed_ref      = ft.Ref[ft.Text]()
        rpm_ref        = ft.Ref[ft.Text]()
        gear_ref       = ft.Ref[ft.Text]()
        throttle_ref   = ft.Ref[ft.ProgressBar]()
        brake_ref      = ft.Ref[ft.ProgressBar]()
        pos_ref        = ft.Ref[ft.Text]()
        lap_ref        = ft.Ref[ft.Text]()
        status_ref     = ft.Ref[ft.Text]()
        self._telemetry_refs = {
            "speed": speed_ref, "rpm": rpm_ref, "gear": gear_ref,
            "throttle": throttle_ref, "brake": brake_ref,
            "pos": pos_ref, "lap": lap_ref, "status": status_ref,
        }

        telemetry_card = ft.Container(
            content=ft.Column([
                ft.Row([
                    ft.Text("LIVE TELEMETRÍA", size=11, color=ORANGE,
                            weight=ft.FontWeight.W_700),
                    ft.Container(
                        ref=status_ref,
                        content=ft.Text("Esperando iRacing...", size=11, color=MUTED),
                    ),
                ], alignment=ft.MainAxisAlignment.SPACE_BETWEEN),
                ft.Container(height=14),
                ft.Row([
                    # Velocidad
                    ft.Container(
                        content=ft.Column([
                            ft.Text("VELOCIDAD", size=9, color=MUTED),
                            ft.Text(ref=speed_ref, value="--- km/h", size=32,
                                    weight=ft.FontWeight.W_900, color=ORANGE),
                        ], spacing=4, horizontal_alignment=ft.CrossAxisAlignment.CENTER),
                        expand=True, alignment=ft.Alignment(0, 0),
                    ),
                    ft.Container(width=1, bgcolor=BORDER2, height=70),
                    # RPM
                    ft.Container(
                        content=ft.Column([
                            ft.Text("RPM", size=9, color=MUTED),
                            ft.Text(ref=rpm_ref, value="----", size=32,
                                    weight=ft.FontWeight.W_900, color=TEXT),
                        ], spacing=4, horizontal_alignment=ft.CrossAxisAlignment.CENTER),
                        expand=True, alignment=ft.Alignment(0, 0),
                    ),
                    ft.Container(width=1, bgcolor=BORDER2, height=70),
                    # Marcha
                    ft.Container(
                        content=ft.Column([
                            ft.Text("MARCHA", size=9, color=MUTED),
                            ft.Text(ref=gear_ref, value="N", size=40,
                                    weight=ft.FontWeight.W_900, color=CYAN),
                        ], spacing=4, horizontal_alignment=ft.CrossAxisAlignment.CENTER),
                        expand=True, alignment=ft.Alignment(0, 0),
                    ),
                ], spacing=0),
                ft.Container(height=14),
                ft.Column([
                    ft.Row([
                        ft.Text("GAS", size=10, color=GREEN, weight=ft.FontWeight.W_600, width=40),
                        ft.ProgressBar(ref=throttle_ref, value=0, color=GREEN,
                                       bgcolor=SURFACE3, height=12,
                                       expand=True, border_radius=6),
                    ], spacing=10),
                    ft.Row([
                        ft.Text("FRENO", size=10, color=DANGER, weight=ft.FontWeight.W_600, width=40),
                        ft.ProgressBar(ref=brake_ref, value=0, color=DANGER,
                                       bgcolor=SURFACE3, height=12,
                                       expand=True, border_radius=6),
                    ], spacing=10),
                ], spacing=8),
                ft.Container(height=12),
                ft.Row([
                    ft.Column([
                        ft.Text("POSICIÓN", size=9, color=MUTED),
                        ft.Text(ref=pos_ref, value="P--", size=18, color=WARNING,
                                weight=ft.FontWeight.W_700),
                    ], spacing=3, horizontal_alignment=ft.CrossAxisAlignment.CENTER),
                    ft.Column([
                        ft.Text("VUELTA", size=9, color=MUTED),
                        ft.Text(ref=lap_ref, value="--/--", size=18, color=TEXT,
                                weight=ft.FontWeight.W_700),
                    ], spacing=3, horizontal_alignment=ft.CrossAxisAlignment.CENTER),
                ], alignment=ft.MainAxisAlignment.CENTER, spacing=40),
            ], spacing=0),
            bgcolor=SURFACE,
            border_radius=14,
            border=ft.border.all(1, with_alpha(ORANGE, 0.2)),
            padding=20,
        )

        start_btn = primary_button(
            "Iniciar captura", ft.Icons.PLAY_CIRCLE_OUTLINE_ROUNDED,
            accent=ORANGE,
            on_click=lambda e: self._start_logger(e),
        )
        stop_btn = secondary_button(
            "Detener", ft.Icons.STOP_CIRCLE_OUTLINED,
            accent=DANGER,
            on_click=lambda e: self._stop_logger(),
        )

        info = ft.Container(
            content=ft.Column([
                ft.Row([
                    ft.Icon(ft.Icons.INFO_OUTLINE_ROUNDED, color=ORANGE, size=16),
                    ft.Text("Para ver telemetría en tiempo real, iRacing debe estar abierto y en pista.",
                            size=12, color=MUTED, expand=True),
                ], spacing=8),
            ]),
            bgcolor=with_alpha(ORANGE, 0.06),
            border=ft.border.all(1, with_alpha(ORANGE, 0.2)),
            border_radius=10,
            padding=12,
        )

        return ft.Container(
            content=ft.Column([
                ft.Container(height=12),
                info,
                ft.Container(height=12),
                telemetry_card,
                ft.Container(height=14),
                ft.Row([start_btn, stop_btn], spacing=10),
            ], spacing=0, scroll=ft.ScrollMode.AUTO, expand=True),
            expand=True,
        )

    # ─── Logger control ───────────────────────────────────────────────────────
    def _logger_toggle_btn(self, running: bool) -> ft.Control:
        label_ref = ft.Ref[ft.Text]()
        dot_ref   = ft.Ref[ft.Container]()

        def toggle(e):
            r = self.state.get("tracker_running", False)
            if r:
                self._stop_logger()
                label_ref.current.value = "Logger Offline"
                dot_ref.current.bgcolor = DANGER
                self.state["tracker_running"] = False
            else:
                self._start_logger(e)
                label_ref.current.value = "Logger Online"
                dot_ref.current.bgcolor = SUCCESS
                self.state["tracker_running"] = True
            e.control.bgcolor = DANGER if self.state.get("tracker_running") else SUCCESS
            self.page.update()

        return ft.ElevatedButton(
            content=ft.Row([
                ft.Container(ref=dot_ref, width=8, height=8,
                             bgcolor=SUCCESS if running else DANGER, border_radius=4),
                ft.Text(ref=label_ref,
                        value="Logger Online" if running else "Logger Offline",
                        size=12, color="white", weight=ft.FontWeight.W_600),
            ], spacing=8, tight=True),
            bgcolor=DANGER if running else SUCCESS,
            style=ft.ButtonStyle(shape=ft.RoundedRectangleBorder(radius=10), elevation=0),
            on_click=toggle,
        )

    def _start_logger(self, e=None):
        if TRACKER_BASE not in sys.path:
            sys.path.insert(0, TRACKER_BASE)

        def run():
            try:
                from iracing_logger import iRacingLogger
                logger = iRacingLogger()
                self.state["_logger_instance"] = logger
                logger.run()
            except Exception as ex:
                print(f"Logger error: {ex}")

        t = threading.Thread(target=run, daemon=True)
        t.start()
        self.state["_logger_thread"] = t
        self.state["tracker_running"] = True

    def _stop_logger(self):
        self.state["tracker_running"] = False

    def _import_history(self, e):
        if TRACKER_BASE not in sys.path:
            sys.path.insert(0, TRACKER_BASE)
        def run():
            try:
                import subprocess
                subprocess.run(
                    [sys.executable, os.path.join(TRACKER_BASE, "import_history.py")],
                    cwd=TRACKER_BASE,
                )
            except Exception as ex:
                print(f"Import error: {ex}")
        threading.Thread(target=run, daemon=True).start()
