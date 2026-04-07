import flet as ft
from core.contracts import get_available_offers, all_requirements_met
from data import database as db


class ContractsView:
    def __init__(self, data, colors, engine):
        self.data = data or {}
        self.c = colors
        self.engine = engine

    def build(self) -> ft.Control:
        stats = self.data.get("stats", {})
        races = self.data.get("recent_races", [])
        wins = sum(1 for r in races if r.get("finish_position") == 1)
        irating = stats.get("irating", 0)
        sr = stats.get("safety_rating", 0.0)

        offers = get_available_offers(irating, sr, wins)
        cards = [self._team_card(t, irating, sr, wins) for t in offers]

        return ft.Column(
            [
                ft.Text("OFERTAS DE EQUIPOS", size=10, color=self.c["muted"],
                        weight=ft.FontWeight.W_500),
                ft.Column(cards, spacing=10),
            ],
            spacing=12, scroll=ft.ScrollMode.AUTO,
        )

    def _team_card(self, team, irating, sr, wins) -> ft.Container:
        reqs = team["requirements_check"]
        met = all_requirements_met(team, irating, sr, wins)

        req_pills = ft.Row([
            self._req_pill(f"SR ≥ {reqs['sr']['needed']}", reqs['sr']['ok']),
            self._req_pill(f"iR ≥ {reqs['irating']['needed']}", reqs['irating']['ok']),
            self._req_pill(f"{reqs['wins']['needed']} vic.", reqs['wins']['ok']),
        ], spacing=6, wrap=True)

        return ft.Container(
            content=ft.Column([
                ft.Row([
                    ft.Column([
                        ft.Text(team["name"], size=13, weight=ft.FontWeight.W_500,
                                color=self.c["text"]),
                        ft.Text(team["description"], size=11, color=self.c["muted"]),
                    ], expand=True),
                    ft.Text(f"${team['salary_per_race']:,}/carrera",
                            size=13, weight=ft.FontWeight.W_500,
                            color=self.c["green"]),
                ]),
                req_pills,
                ft.ElevatedButton(
                    "Firmar contrato" if met else "Requisitos no cumplidos",
                    disabled=not met,
                    style=ft.ButtonStyle(
                        bgcolor=self.c["purple"] if met else self.c["surface2"],
                        color=ft.Colors.WHITE if met else self.c["muted"],
                    ),
                ),
            ], spacing=8),
            bgcolor=self.c["surface"],
            border_radius=8,
            border=ft.border.all(
                1 if met else 0.5,
                self.c["purple"] + "99" if met else self.c["border"],
            ),
            padding=14,
        )

    def _req_pill(self, text, ok) -> ft.Container:
        color = self.c["green"] if ok else self.c["red"]
        icon = "✓" if ok else "✗"
        return ft.Container(
            content=ft.Text(f"{text} {icon}", size=10, color=color),
            bgcolor=color + "18",
            border=ft.border.all(0.5, color + "55"),
            border_radius=10,
            padding=ft.padding.symmetric(horizontal=8, vertical=3),
        )
