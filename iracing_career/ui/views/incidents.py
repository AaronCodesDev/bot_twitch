import flet as ft
from core.sanctions import WEEKLY_INCIDENT_LIMIT, SERIOUS_ACCIDENT_THRESHOLD


class IncidentsView:
    def __init__(self, data, colors, engine):
        self.data = data or {}
        self.c = colors

    def build(self) -> ft.Control:
        races = self.data.get("recent_races", [])

        total_inc = sum(r.get("incidents", 0) for r in races)
        serious = [r for r in races if r.get("incidents", 0) >= SERIOUS_ACCIDENT_THRESHOLD]
        weekly_inc = sum(r.get("incidents", 0) for r in races[:5])

        penalties = sum(
            r.get("incidents", 0) * 50
            for r in races if r.get("incidents", 0) > 0
        )

        weekly_pct = min(weekly_inc / WEEKLY_INCIDENT_LIMIT, 1.0)
        weekly_color = (self.c["red"] if weekly_pct >= 1
                        else self.c["amber"] if weekly_pct >= 0.7
                        else self.c["green"])

        return ft.Column(
            [
                # Resumen
                ft.Container(
                    content=ft.Column([
                        ft.Text("RESUMEN DE INCIDENTES", size=10, color=self.c["muted"],
                                weight=ft.FontWeight.W_500),
                        ft.Divider(height=1, color=self.c["border"]),
                        self._info_row("Total incidentes", str(total_inc), self.c["amber"]),
                        self._info_row("Accidentes graves", str(len(serious)), self.c["red"]),
                        self._info_row("Carreras afectadas",
                                       f"{len([r for r in races if r.get('incidents',0)>0])} de {len(races)}",
                                       self.c["text"]),
                        self._info_row("Penalización económica",
                                       f"-${penalties:,}", self.c["red"]),
                    ], spacing=8),
                    bgcolor=self.c["surface"],
                    border_radius=8,
                    border=ft.border.all(0.5, self.c["border"]),
                    padding=12,
                ),

                # Umbrales
                ft.Container(
                    content=ft.Column([
                        ft.Text("UMBRALES DE SANCIÓN", size=10, color=self.c["muted"],
                                weight=ft.FontWeight.W_500),
                        ft.Column([
                            ft.Row([
                                ft.Text("Incidentes esta semana", size=11,
                                        color=self.c["muted"], expand=True),
                                ft.Text(f"{weekly_inc}x / {WEEKLY_INCIDENT_LIMIT}x límite",
                                        size=11, color=weekly_color,
                                        weight=ft.FontWeight.W_500),
                            ]),
                            ft.ProgressBar(value=weekly_pct, color=weekly_color,
                                           bgcolor=self.c["surface2"],
                                           height=5, border_radius=2),
                            ft.Text(f"Superar {WEEKLY_INCIDENT_LIMIT}x activa reposo de 3 días",
                                    size=10, color=self.c["muted"]),
                        ], spacing=5),
                    ], spacing=10),
                    bgcolor=self.c["surface"],
                    border_radius=8,
                    border=ft.border.all(0.5, self.c["border"]),
                    padding=12,
                ),

                # Lista de carreras con incidentes
                ft.Container(
                    content=ft.Column([
                        ft.Text("CARRERAS CON INCIDENTES", size=10, color=self.c["muted"],
                                weight=ft.FontWeight.W_500),
                        *[self._race_row(r) for r in races if r.get("incidents", 0) > 0],
                    ], spacing=4),
                    bgcolor=self.c["surface"],
                    border_radius=8,
                    border=ft.border.all(0.5, self.c["border"]),
                    padding=12,
                ),
            ],
            spacing=10, scroll=ft.ScrollMode.AUTO,
        )

    def _info_row(self, label, value, color) -> ft.Row:
        return ft.Row([
            ft.Text(label, size=11, color=self.c["muted"], expand=True),
            ft.Text(value, size=11, color=color, weight=ft.FontWeight.W_500),
        ])

    def _race_row(self, r) -> ft.Container:
        inc = r.get("incidents", 0)
        color = self.c["red"] if inc >= SERIOUS_ACCIDENT_THRESHOLD else self.c["amber"]
        return ft.Container(
            content=ft.Row([
                ft.Container(
                    content=ft.Text(f"{inc}x", size=11, color=color,
                                    weight=ft.FontWeight.W_500),
                    width=36, height=26,
                    bgcolor=color + "18",
                    border=ft.border.all(0.5, color + "44"),
                    border_radius=6,
                    alignment=ft.alignment.center,
                ),
                ft.Text(r.get("track", ""), size=12, color=self.c["text"], expand=True),
                ft.Text(f"-${inc*50:,}", size=11, color=self.c["red"]),
            ], spacing=8),
            border=ft.border.only(bottom=ft.BorderSide(0.5, self.c["border"])),
            padding=ft.padding.symmetric(vertical=5),
        )
