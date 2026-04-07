# ui/views/home_view.py
# Vista principal — Hub overview  (Redesign v3 — Responsive)

import flet as ft
import sqlite3
import os
from datetime import datetime
from ui.colors import *
from ui.components import *


BASE       = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
TWITCH_DB  = os.path.join(BASE, "bot_twitch",     "data", "database.db")
TRACKER_DB = os.path.join(BASE, "iracing_tracker", "iracing_data.db")
CAREER_DB  = os.path.join(BASE, "iracing_career",  "data", "career.db")


def _q(db_path: str, query: str, default=None):
    try:
        if not os.path.exists(db_path):
            return default
        conn = sqlite3.connect(db_path)
        conn.row_factory = sqlite3.Row
        r = conn.cursor().execute(query).fetchone()
        conn.close()
        return r[0] if r and r[0] is not None else default
    except Exception:
        return default


def _qa(db_path: str, query: str):
    try:
        if not os.path.exists(db_path):
            return []
        conn = sqlite3.connect(db_path)
        conn.row_factory = sqlite3.Row
        rows = conn.cursor().execute(query).fetchall()
        conn.close()
        return [dict(r) for r in rows]
    except Exception:
        return []


class HomeView:
    def __init__(self, state: dict, on_navigate):
        self.state  = state
        self.on_nav = on_navigate

    # ─── Build ────────────────────────────────────────────────────────────────
    def build(self) -> ft.Control:
        # ── Datos ─────────────────────────────────────────────────────────────
        total_subs  = _q(TWITCH_DB,  "SELECT COUNT(*) FROM subscribers", 0) or 0
        tier3_subs  = _q(TWITCH_DB,  "SELECT COUNT(*) FROM subscribers WHERE tier=3", 0) or 0
        total_users = _q(TWITCH_DB,  "SELECT COUNT(*) FROM users", 0) or 0

        total_sessions = _q(TRACKER_DB, "SELECT COUNT(*) FROM sessions", 0) or 0
        best_irating   = _q(TRACKER_DB,
            "SELECT MAX(irating_before) FROM sessions WHERE irating_before > 0", 0) or 0
        wins_tracker   = _q(TRACKER_DB,
            "SELECT COUNT(*) FROM sessions WHERE finish_position = 1", 0) or 0

        career_balance = _q(CAREER_DB, "SELECT balance FROM pilots LIMIT 1", 48200) or 48200
        career_races   = _q(CAREER_DB, "SELECT COUNT(*) FROM results", 0) or 0
        career_wins    = _q(CAREER_DB,
            "SELECT COUNT(*) FROM results WHERE finish_position=1", 0) or 0
        career_name    = _q(CAREER_DB, "SELECT name FROM pilots LIMIT 1", "Demo Piloto") or "Demo Piloto"
        career_rep     = _q(CAREER_DB, "SELECT reputation FROM pilots LIMIT 1", 62) or 62

        owned_items    = _qa(CAREER_DB,
            "SELECT item_name FROM owned_item WHERE pilot_id=1 ORDER BY bought_at DESC LIMIT 3")

        bot_on     = self.state.get("bot_running",     False)
        tracker_on = self.state.get("tracker_running", False)

        recent_subs = _qa(TWITCH_DB,
            "SELECT username, tier, meses FROM subscribers ORDER BY fecha DESC LIMIT 4")
        recent_sess = _qa(TRACKER_DB,
            "SELECT track_name, finish_position, irating_change FROM sessions "
            "ORDER BY session_date DESC LIMIT 4")

        now      = datetime.now()
        greeting = "Buenos días" if now.hour < 12 else ("Buenas tardes" if now.hour < 20 else "Buenas noches")

        # ── Layout principal ──────────────────────────────────────────────────
        # Fila superior: hero + career card (lado a lado)
        top_row = ft.Row([
            self._build_hero(greeting, bot_on, tracker_on),
            self._build_career_card(
                career_name, career_balance, career_rep,
                career_races, career_wins, owned_items,
            ),
        ], spacing=14, expand=False)

        # Fila de módulos
        module_row = ft.Row([
            self._module_card(
                "🟣", "Twitch Bot", "fantan · bot_fantan", PURPLE,
                "Online" if bot_on else "Offline", bot_on,
                [("👥", "Subs", str(total_subs)),
                 ("💜", "Tier 3", str(tier3_subs)),
                 ("🤖", "Usuarios", str(total_users))],
                "twitch",
            ),
            self._module_card(
                "🏎️", "iRacing Tracker", "Telemetría & estadísticas", ORANGE,
                "Con datos" if total_sessions > 0 else "Sin datos", total_sessions > 0,
                [("🏁", "Sesiones", str(total_sessions)),
                 ("📈", "iRating",  str(best_irating) if best_irating else "---"),
                 ("🥇", "Victorias", str(wins_tracker))],
                "tracker",
            ),
            self._module_card(
                "🏆", "iRacing Career", "Modo carrera virtual", GREEN,
                "Activo" if career_races > 0 else "Demo", True,
                [("💰", "Balance", f"${career_balance:,.0f}"),
                 ("🏁", "Carreras", str(career_races)),
                 ("🥇", "Victorias", str(career_wins))],
                "career",
            ),
        ], spacing=14, expand=True)

        # Fila inferior: actividad + resumen
        bottom_row = self._build_bottom(recent_subs, recent_sess,
                                        total_subs, total_sessions,
                                        career_balance, total_users)

        return ft.Column([
            top_row,
            ft.Container(height=14),
            module_row,
            ft.Container(height=14),
            bottom_row,
        ], spacing=0, scroll=ft.ScrollMode.AUTO, expand=True)

    # ─── Hero (saludo) ────────────────────────────────────────────────────────
    def _build_hero(self, greeting: str, bot_on: bool, tracker_on: bool) -> ft.Container:
        return ft.Container(
            content=ft.Column([
                # Pills de estado
                ft.Row([
                    self._pill("Bot",     bot_on,     PURPLE),
                    self._pill("Logger",  tracker_on, ORANGE),
                    self._pill("Career",  True,       GREEN),
                ], spacing=6),
                ft.Container(height=10),
                ft.Text(f"{greeting}, Fantan 👋",
                        size=22, weight=ft.FontWeight.W_800, color=TEXT),
                ft.Text("Tu hub personal de streaming & iRacing",
                        size=12, color=MUTED),
                ft.Container(height=14),
                ft.Row([
                    self._hero_chip("🟣", "Twitch Bot", PURPLE, "twitch"),
                    self._hero_chip("🏎️", "iR Tracker", ORANGE, "tracker"),
                    self._hero_chip("🏆", "iR Career",  GREEN,  "career"),
                ], spacing=8),
            ], spacing=2),
            bgcolor=SURFACE,
            border_radius=18,
            border=ft.border.all(1, with_alpha(CYAN, 0.2)),
            padding=ft.padding.symmetric(horizontal=22, vertical=18),
            expand=True,
            gradient=ft.LinearGradient(
                begin=ft.Alignment(-1, -1),
                end=ft.Alignment(1, 1),
                colors=[with_alpha(CYAN, 0.07), with_alpha(PURPLE, 0.03)],
            ),
        )

    def _pill(self, label: str, active: bool, accent: str) -> ft.Container:
        c = accent if active else MUTED2
        return ft.Container(
            content=ft.Row([
                ft.Container(width=6, height=6, bgcolor=c, border_radius=3),
                ft.Text(label, size=10, color=c, weight=ft.FontWeight.W_600),
            ], spacing=5),
            bgcolor=with_alpha(c, 0.1),
            border=ft.border.all(1, with_alpha(c, 0.25)),
            border_radius=20,
            padding=ft.padding.symmetric(horizontal=9, vertical=3),
        )

    def _hero_chip(self, emoji, label, accent, nav_id) -> ft.Container:
        return ft.Container(
            content=ft.Row([
                ft.Text(emoji, size=12),
                ft.Text(label, size=11, color=accent, weight=ft.FontWeight.W_600),
            ], spacing=5),
            bgcolor=with_alpha(accent, 0.1),
            border=ft.border.all(1, with_alpha(accent, 0.3)),
            border_radius=20,
            padding=ft.padding.symmetric(horizontal=12, vertical=6),
            on_click=lambda e, nid=nav_id: self.on_nav(nid),
        )

    # ─── Career snapshot card ─────────────────────────────────────────────────
    def _build_career_card(self, name, balance, rep, races, wins, owned_items) -> ft.Container:
        # Iniciales del piloto
        initials = "".join(p[0].upper() for p in str(name).split()[:2]) or "FP"

        avatar = ft.Container(
            content=ft.Text(initials, size=16, weight=ft.FontWeight.W_900, color=TEXT),
            width=52, height=52,
            border_radius=26,
            alignment=ft.Alignment(0, 0),
            gradient=ft.LinearGradient(
                begin=ft.Alignment(-1, -1), end=ft.Alignment(1, 1),
                colors=[with_alpha(GREEN, 0.5), with_alpha(CYAN, 0.35)],
            ),
        )

        rep_pct = min(max(rep / 100, 0), 1)
        rep_color = GREEN if rep >= 60 else (WARNING if rep >= 30 else DANGER)

        # Items comprados (demo si no hay)
        demo_items = [
            {"item_name": "Mejora de setup", "icon": "🔧"},
            {"item_name": "Data engineer",   "icon": "📊"},
            {"item_name": "Simulador avanz.", "icon": "🖥️"},
        ]
        icon_map = {
            "Mejora de setup básico": "🔧", "Data engineer": "📊",
            "Simulador avanzado": "🖥️",    "Nutricionista": "🥗",
            "Mecánico elite": "⚙️",         "Windtunnel session": "💨",
        }

        items_show = []
        if owned_items:
            for it in owned_items[:3]:
                n = it.get("item_name", "Ítem")
                items_show.append((icon_map.get(n, "📦"), n[:20]))
        else:
            for it in demo_items:
                items_show.append((it["icon"], it["item_name"]))

        items_row = ft.Row([
            ft.Container(
                content=ft.Row([
                    ft.Text(ico, size=13),
                    ft.Text(nm, size=10, color=MUTED),
                ], spacing=5),
                bgcolor=with_alpha(CYAN, 0.07),
                border_radius=8,
                padding=ft.padding.symmetric(horizontal=8, vertical=4),
                border=ft.border.all(1, with_alpha(CYAN, 0.15)),
            )
            for ico, nm in items_show
        ], spacing=6, wrap=True)

        return ft.Container(
            content=ft.Column([
                # Header del piloto
                ft.Row([
                    avatar,
                    ft.Column([
                        ft.Text(name, size=13, weight=ft.FontWeight.W_800, color=TEXT),
                        ft.Text("iRacing Career", size=10, color=MUTED),
                    ], spacing=2, expand=True),
                    ft.Container(
                        content=ft.Column([
                            ft.Text(f"${balance:,.0f}", size=14,
                                    weight=ft.FontWeight.W_800, color=GREEN),
                            ft.Text("Balance", size=9, color=MUTED),
                        ], spacing=1, horizontal_alignment=ft.CrossAxisAlignment.END),
                    ),
                ], spacing=10),

                ft.Container(height=10),

                # Stats rápidas
                ft.Row([
                    self._mini_num(str(races),  "Carreras", ORANGE),
                    self._mini_num(str(wins),   "Victorias", WARNING),
                    self._mini_num(f"{rep}",    "Reputación", rep_color),
                ], spacing=10),

                ft.Container(height=8),

                # Barra de reputación
                ft.Column([
                    ft.Row([
                        ft.Text("Reputación", size=9, color=MUTED),
                        ft.Text(f"{rep}/100", size=9, color=rep_color,
                                weight=ft.FontWeight.W_700),
                    ], alignment=ft.MainAxisAlignment.SPACE_BETWEEN),
                    ft.ProgressBar(value=rep_pct, color=rep_color,
                                   bgcolor=SURFACE3, height=5, border_radius=3),
                ], spacing=4),

                ft.Container(height=10),

                # Posesiones
                ft.Text("📦 Posesiones", size=10, color=MUTED, weight=ft.FontWeight.W_600),
                ft.Container(height=4),
                items_row,

                ft.Container(height=10),

                # Botón ir a perfil
                ft.Container(
                    content=ft.Row([
                        ft.Text("Ver perfil completo →", size=11, color=GREEN,
                                weight=ft.FontWeight.W_700),
                    ]),
                    on_click=lambda e: self.on_nav("career"),
                    padding=ft.padding.symmetric(vertical=2),
                ),
            ], spacing=0),
            bgcolor=SURFACE,
            border_radius=18,
            border=ft.border.all(1, with_alpha(GREEN, 0.25)),
            padding=ft.padding.symmetric(horizontal=18, vertical=16),
            width=310,
            gradient=ft.LinearGradient(
                begin=ft.Alignment(-1, -1),
                end=ft.Alignment(1, 1),
                colors=[with_alpha(GREEN, 0.06), with_alpha(CYAN, 0.02)],
            ),
        )

    def _mini_num(self, value: str, label: str, accent: str) -> ft.Container:
        return ft.Container(
            content=ft.Column([
                ft.Text(value, size=16, weight=ft.FontWeight.W_800, color=accent),
                ft.Text(label, size=9,  color=MUTED),
            ], spacing=1, horizontal_alignment=ft.CrossAxisAlignment.CENTER),
            bgcolor=with_alpha(accent, 0.08),
            border_radius=10,
            padding=ft.padding.symmetric(horizontal=10, vertical=8),
            expand=True,
            alignment=ft.Alignment(0, 0),
        )

    # ─── Module cards ─────────────────────────────────────────────────────────
    def _module_card(self, emoji, title, subtitle, accent,
                     status, status_ok, stats, nav_id) -> ft.Container:
        stat_cols = [
            ft.Column([
                ft.Row([
                    ft.Text(ic, size=12),
                    ft.Text(val, size=14, weight=ft.FontWeight.W_800, color=TEXT),
                ], spacing=4),
                ft.Text(lbl, size=9, color=MUTED),
            ], spacing=2, horizontal_alignment=ft.CrossAxisAlignment.CENTER)
            for ic, lbl, val in stats
        ]

        return ft.Container(
            content=ft.Column([
                ft.Row([
                    ft.Container(
                        content=ft.Text(emoji, size=22),
                        width=44, height=44,
                        bgcolor=with_alpha(accent, 0.12),
                        border_radius=12,
                        alignment=ft.Alignment(0, 0),
                        border=ft.border.all(1, with_alpha(accent, 0.2)),
                    ),
                    ft.Column([
                        ft.Text(title,    size=13, weight=ft.FontWeight.W_800, color=TEXT),
                        ft.Text(subtitle, size=10, color=MUTED),
                    ], spacing=2, expand=True),
                    ft.Container(
                        content=ft.Row([
                            ft.Container(width=6, height=6,
                                         bgcolor=accent if status_ok else MUTED2,
                                         border_radius=3),
                            ft.Text(status, size=10,
                                    color=accent if status_ok else MUTED,
                                    weight=ft.FontWeight.W_600),
                        ], spacing=4),
                        bgcolor=with_alpha(accent if status_ok else MUTED2, 0.08),
                        border_radius=10,
                        padding=ft.padding.symmetric(horizontal=8, vertical=4),
                    ),
                ], spacing=10),
                ft.Container(height=12),
                ft.Container(height=1, bgcolor=BORDER2),
                ft.Container(height=12),
                ft.Row(stat_cols, alignment=ft.MainAxisAlignment.SPACE_AROUND),
                ft.Container(height=14),
                ft.Container(
                    content=ft.Row([
                        ft.Text("Abrir módulo", size=11, color=accent,
                                weight=ft.FontWeight.W_700),
                        ft.Icon(ft.Icons.ARROW_FORWARD_ROUNDED, size=13, color=accent),
                    ], spacing=4),
                    on_click=lambda e, nid=nav_id: self.on_nav(nid),
                ),
            ], spacing=0),
            bgcolor=SURFACE,
            border_radius=16,
            border=ft.border.all(1, with_alpha(accent, 0.18)),
            padding=ft.padding.symmetric(horizontal=18, vertical=16),
            expand=True,
            gradient=ft.LinearGradient(
                begin=ft.Alignment(-1, -1), end=ft.Alignment(1, 1),
                colors=[SURFACE, with_alpha(accent, 0.03)],
            ),
            on_hover=lambda e, a=accent: (
                setattr(e.control, "border",
                    ft.border.all(1, with_alpha(a, 0.55) if e.data == "true"
                                  else with_alpha(a, 0.18))),
                e.control.update()
            ),
        )

    # ─── Bottom: actividad + resumen ──────────────────────────────────────────
    def _build_bottom(self, recent_subs, recent_sess,
                      total_subs, total_sessions, career_balance, total_users) -> ft.Row:

        items = []
        for s in recent_subs[:3]:
            tier = s.get("tier", 1)
            tc   = {1: GREEN, 2: INFO, 3: PURPLE}
            tl   = {1: "T1",  2: "T2", 3: "T3"}
            init = str(s.get("username", "?"))[0].upper()
            items.append(self._activity_item(
                init, tc.get(tier, GREEN),
                s.get("username", "?"),
                f"Sub {tl.get(tier,'T1')} · {s.get('meses',1)} mes(es)",
                "Twitch", PURPLE, False,
            ))
        for r in recent_sess[:3]:
            change = r.get("irating_change", 0) or 0
            sign   = "+" if change >= 0 else ""
            track  = (r.get("track_name") or "?")[:22]
            items.append(self._activity_item(
                "🏎", ORANGE, track,
                f"P{r.get('finish_position','?')} · iR {sign}{change}",
                "Tracker", ORANGE, True,
            ))

        if not items:
            items = [ft.Container(
                content=ft.Column([
                    ft.Text("🏁", size=32, text_align=ft.TextAlign.CENTER),
                    ft.Text("Sin actividad reciente", size=12, color=MUTED,
                            text_align=ft.TextAlign.CENTER),
                ], horizontal_alignment=ft.CrossAxisAlignment.CENTER, spacing=6),
                padding=ft.padding.symmetric(vertical=24),
                alignment=ft.Alignment(0, 0),
            )]

        activity = ft.Container(
            content=ft.Column([
                ft.Row([
                    ft.Row([
                        ft.Container(width=3, height=14, bgcolor=CYAN, border_radius=2),
                        ft.Text("Actividad reciente", size=13,
                                weight=ft.FontWeight.W_700, color=TEXT),
                    ], spacing=8),
                    ft.Container(
                        content=ft.Row([
                            ft.Container(width=5, height=5, bgcolor=CYAN, border_radius=3),
                            ft.Text("En vivo", size=9, color=CYAN, weight=ft.FontWeight.W_600),
                        ], spacing=4),
                        bgcolor=with_alpha(CYAN, 0.08),
                        border_radius=10,
                        padding=ft.padding.symmetric(horizontal=9, vertical=4),
                    ),
                ], alignment=ft.MainAxisAlignment.SPACE_BETWEEN),
                ft.Container(height=12),
                ft.Column(items[:6], spacing=6),
            ], spacing=0),
            bgcolor=SURFACE,
            border_radius=16,
            border=ft.border.all(1, BORDER2),
            padding=ft.padding.symmetric(horizontal=18, vertical=16),
            expand=True,
        )

        resumen = ft.Container(
            content=ft.Column([
                ft.Row([
                    ft.Container(width=3, height=14, bgcolor=PURPLE, border_radius=2),
                    ft.Text("Resumen", size=13, weight=ft.FontWeight.W_700, color=TEXT),
                ], spacing=8),
                ft.Container(height=12),
                self._mini_stat("👥", "Total subs",    str(total_subs),    PURPLE),
                ft.Container(height=7),
                self._mini_stat("🏁", "Sesiones iR",  str(total_sessions), ORANGE),
                ft.Container(height=7),
                self._mini_stat("💰", "Balance Career", f"${career_balance:,.0f}", GREEN),
                ft.Container(height=7),
                self._mini_stat("🤖", "Usuarios bot",  str(total_users),    CYAN),
                ft.Container(height=16),
                ft.Container(
                    content=ft.Column([
                        ft.Text("⚡", size=26, text_align=ft.TextAlign.CENTER),
                        ft.Text("FanTan Hub", size=12, weight=ft.FontWeight.W_700,
                                color=TEXT, text_align=ft.TextAlign.CENTER),
                        ft.Text("v1.0 · All systems go", size=9, color=MUTED,
                                text_align=ft.TextAlign.CENTER),
                    ], spacing=3, horizontal_alignment=ft.CrossAxisAlignment.CENTER),
                    bgcolor=with_alpha(CYAN, 0.05),
                    border_radius=12,
                    border=ft.border.all(1, with_alpha(CYAN, 0.12)),
                    padding=ft.padding.symmetric(vertical=14),
                    alignment=ft.Alignment(0, 0),
                ),
            ], spacing=0),
            bgcolor=SURFACE,
            border_radius=16,
            border=ft.border.all(1, BORDER2),
            padding=ft.padding.symmetric(horizontal=18, vertical=16),
            width=220,
        )

        return ft.Row([activity, resumen], spacing=14, expand=True)

    # ─── Helpers ──────────────────────────────────────────────────────────────
    def _activity_item(self, letter, accent, text, sub,
                       tag, tag_color, is_emoji) -> ft.Container:
        if is_emoji:
            av = ft.Container(
                content=ft.Text(letter, size=14),
                width=34, height=34,
                bgcolor=with_alpha(accent, 0.12),
                border_radius=9,
                alignment=ft.Alignment(0, 0),
            )
        else:
            av = ft.Container(
                content=ft.Text(letter, size=13, weight=ft.FontWeight.W_800, color=accent),
                width=34, height=34,
                bgcolor=with_alpha(accent, 0.15),
                border_radius=9,
                alignment=ft.Alignment(0, 0),
            )
        return ft.Container(
            content=ft.Row([
                av,
                ft.Column([
                    ft.Text(text, size=12, weight=ft.FontWeight.W_600, color=TEXT),
                    ft.Text(sub,  size=10, color=MUTED),
                ], spacing=1, expand=True),
                ft.Container(
                    content=ft.Text(tag, size=9, color="white", weight=ft.FontWeight.W_700),
                    bgcolor=with_alpha(tag_color, 0.85),
                    border_radius=7,
                    padding=ft.padding.symmetric(horizontal=7, vertical=3),
                ),
            ], spacing=8),
            bgcolor=SURFACE2,
            border_radius=10,
            border=ft.border.only(left=ft.BorderSide(2, accent)),
            padding=ft.padding.symmetric(horizontal=10, vertical=8),
        )

    def _mini_stat(self, emoji, label, value, accent) -> ft.Container:
        return ft.Container(
            content=ft.Row([
                ft.Container(
                    content=ft.Text(emoji, size=13),
                    width=32, height=32,
                    bgcolor=with_alpha(accent, 0.1),
                    border_radius=9,
                    alignment=ft.Alignment(0, 0),
                ),
                ft.Column([
                    ft.Text(label, size=9,  color=MUTED),
                    ft.Text(value, size=13, weight=ft.FontWeight.W_700, color=TEXT),
                ], spacing=1, expand=True),
            ], spacing=8),
            bgcolor=SURFACE2,
            border_radius=10,
            border=ft.border.all(1, with_alpha(accent, 0.12)),
            padding=ft.padding.symmetric(horizontal=10, vertical=7),
        )
