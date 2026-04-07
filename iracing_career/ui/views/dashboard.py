import flet as ft
from core.economy import format_money


class DashboardView:
    def __init__(self, data: dict, colors: dict, engine):
        self.data = data or {}
        self.c = colors
        self.engine = engine

    def build(self) -> ft.Control:
        pilot = self.data.get("pilot", {})
        stats = self.data.get("stats", {})
        races = self.data.get("recent_races", [])
        contract = self.data.get("active_contract")
        is_banned = self.data.get("is_banned", False)

        wins = sum(1 for r in races if r.get("finish_position") == 1)
        season_earnings = sum(r.get("prize_money", 0) for r in races)

        return ft.Column(
            [
                # Aviso si está sancionado
                ft.Container(
                    content=ft.Row([
                        ft.Icon(ft.Icons.DO_NOT_DISTURB, color=self.c["red"], size=16),
                        ft.Text(f"Piloto en reposo — {self.data.get('ban_reason', '')}",
                                color=self.c["red"], size=12),
                    ], spacing=8),
                    bgcolor="#E24B4A0e",
                    border=ft.border.all(0.5, self.c["red"] + "44"),
                    border_radius=8,
                    padding=10,
                    visible=is_banned,
                ),

                # Tarjetas de stats
                ft.Row(
                    [
                        self._stat_card("iRating", str(stats.get("irating", 0)),
                                        self.c["amber"], "+124 esta semana"),
                        self._stat_card("Safety R.", str(stats.get("safety_rating", 0)),
                                        self.c["green"], "Muy limpio"),
                        self._stat_card("Victorias", str(wins),
                                        self.c["text"], "esta temporada"),
                        self._stat_card("Balance",
                                        f"${pilot.get('balance', 0):,.0f}",
                                        self.c["green"],
                                        format_money(season_earnings) + " temporada"),
                    ],
                    spacing=8,
                ),

                # Barras de contrato
                self._contract_progress(stats, contract),

                # Últimas carreras
                ft.Row(
                    [self._recent_races(races), self._quick_info(stats, contract)],
                    spacing=10,
                    expand=True,
                    vertical_alignment=ft.CrossAxisAlignment.START,
                ),
            ],
            spacing=12,
            expand=True,
        )

    def _stat_card(self, label, value, color, sub) -> ft.Container:
        return ft.Container(
            content=ft.Column([
                ft.Text(label.upper(), size=10, color=self.c["muted"],
                        weight=ft.FontWeight.W_500),
                ft.Text(value, size=22, weight=ft.FontWeight.W_500, color=color),
                ft.Text(sub, size=10, color=self.c["green"]),
            ], spacing=3),
            bgcolor=self.c["surface"],
            border_radius=8,
            border=ft.border.all(0.5, self.c["border"]),
            padding=ft.padding.symmetric(horizontal=12, vertical=10),
            expand=True,
        )

    def _contract_progress(self, stats: dict, contract: dict | None) -> ft.Container:
        if not contract:
            return ft.Container(
                content=ft.Text("Sin contrato activo — visita la pestaña Contratos",
                                color=self.c["muted"], size=12),
                bgcolor=self.c["surface"],
                border_radius=8,
                border=ft.border.all(0.5, self.c["border"]),
                padding=12,
            )

        sr = stats.get("safety_rating", 0)
        ir = stats.get("irating", 0)
        sr_pct = min(sr / contract["min_sr"], 1.0) if contract["min_sr"] else 1
        ir_pct = min(ir / contract["min_irating"], 1.0) if contract["min_irating"] else 1

        return ft.Container(
            content=ft.Column([
                ft.Text("Rendimiento en contrato", size=11, color=self.c["muted"],
                        weight=ft.FontWeight.W_500),
                self._progress_bar(f"SR mínimo ({contract['min_sr']})", sr_pct, self.c["green"], str(sr)),
                self._progress_bar(f"iRating req. ({contract['min_irating']})", ir_pct, self.c["amber"], str(ir)),
            ], spacing=8),
            bgcolor=self.c["surface"],
            border_radius=8,
            border=ft.border.all(0.5, self.c["border"]),
            padding=12,
        )

    def _progress_bar(self, label, pct, color, val_text) -> ft.Row:
        return ft.Row([
            ft.Text(label, size=11, color=self.c["muted"], width=160),
            ft.ProgressBar(value=pct, color=color, bgcolor=self.c["surface2"],
                           height=4, expand=True, border_radius=2),
            ft.Text(val_text, size=11, color=color, width=50,
                    text_align=ft.TextAlign.RIGHT),
        ], spacing=8)

    def _recent_races(self, races: list) -> ft.Container:
        rows = []
        for r in races[:5]:
            pos = r.get("finish_position", 0)
            inc = r.get("incidents", 0)
            money = r.get("prize_money", 0)
            pos_color = (self.c["amber"] if pos == 1
                         else self.c["green"] if pos <= 3
                         else self.c["red"] if pos > 40
                         else self.c["muted"])
            pos_label = "DQ" if pos > 40 else str(pos)

            rows.append(ft.Container(
                content=ft.Row([
                    ft.Container(
                        content=ft.Text(pos_label, size=11, weight=ft.FontWeight.W_500,
                                        color=pos_color),
                        width=32, height=28,
                        bgcolor=pos_color + "18",
                        border=ft.border.all(0.5, pos_color + "55"),
                        border_radius=6,
                        alignment=ft.alignment.center,
                    ),
                    ft.Column([
                        ft.Text(r.get("track", ""), size=12,
                                weight=ft.FontWeight.W_500, color=self.c["text"]),
                        ft.Text(f"{inc}x inc · {r.get('series','')[:25]}",
                                size=10, color=self.c["muted"]),
                    ], spacing=1, expand=True),
                    ft.Text(format_money(money), size=12, weight=ft.FontWeight.W_500,
                            color=self.c["green"] if money >= 0 else self.c["red"]),
                ], spacing=8),
                border=ft.border.only(bottom=ft.BorderSide(0.5, self.c["border"])),
                padding=ft.padding.symmetric(vertical=7, horizontal=0),
            ))

        return ft.Container(
            content=ft.Column([
                ft.Text("ÚLTIMAS CARRERAS", size=10, color=self.c["muted"],
                        weight=ft.FontWeight.W_500),
                *rows,
            ], spacing=0),
            bgcolor=self.c["surface"],
            border_radius=8,
            border=ft.border.all(0.5, self.c["border"]),
            padding=12,
            expand=True,
        )

    def _quick_info(self, stats: dict, contract: dict | None) -> ft.Container:
        lic = stats.get("license_class", "?")
        cat = stats.get("category", "Road")
        team = contract["team_name"] if contract else "Freelance"

        return ft.Container(
            content=ft.Column([
                ft.Text("ESTADO", size=10, color=self.c["muted"],
                        weight=ft.FontWeight.W_500),
                ft.Divider(height=1, color=self.c["border"]),
                self._info_row("Licencia", f"Clase {lic} · {cat}"),
                self._info_row("Equipo", team),
                self._info_row("Categoría", cat),
                self._info_row("Reputación", "62 / 100"),
            ], spacing=8),
            bgcolor=self.c["surface"],
            border_radius=8,
            border=ft.border.all(0.5, self.c["border"]),
            padding=12,
            width=200,
        )

    def _info_row(self, label, value) -> ft.Row:
        return ft.Row([
            ft.Text(label, size=11, color=self.c["muted"], expand=True),
            ft.Text(value, size=11, color=self.c["text"], weight=ft.FontWeight.W_500),
        ])
