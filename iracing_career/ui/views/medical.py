import flet as ft


class MedicalView:
    def __init__(self, data, colors, engine):
        self.data = data or {}
        self.c = colors

    def build(self) -> ft.Control:
        sanctions = self.data.get("active_sanctions", [])
        is_banned = self.data.get("is_banned", False)

        if not sanctions:
            return ft.Container(
                content=ft.Column([
                    ft.Icon(ft.Icons.CHECK_CIRCLE_OUTLINE, color=self.c["green"], size=48),
                    ft.Text("Piloto en perfecto estado", size=14,
                            color=self.c["green"], weight=ft.FontWeight.W_500),
                    ft.Text("Sin sanciones ni reposos activos.", size=12,
                            color=self.c["muted"]),
                ], horizontal_alignment=ft.CrossAxisAlignment.CENTER, spacing=8),
                alignment=ft.alignment.center, expand=True,
            )

        cards = [self._sanction_card(s) for s in sanctions]

        recovery_options = ft.Container(
            content=ft.Column([
                ft.Text("OPCIONES DE RECUPERACIÓN", size=10, color=self.c["muted"],
                        weight=ft.FontWeight.W_500),
                ft.Row([
                    self._recovery_option("Médico privado", "Reduce reposo a la mitad", 3500),
                    self._recovery_option("Centro de recuperación", "Bono de forma al volver", 5000),
                ], spacing=8),
            ], spacing=8),
            bgcolor=self.c["surface"],
            border_radius=8,
            border=ft.border.all(0.5, self.c["border"]),
            padding=12,
            visible=is_banned,
        )

        return ft.Column(
            [*cards, recovery_options],
            spacing=10, scroll=ft.ScrollMode.AUTO,
        )

    def _sanction_card(self, s) -> ft.Container:
        icon = (ft.Icons.MEDICAL_SERVICES_OUTLINED
                if s.get("type") == "medical"
                else ft.Icons.BLOCK_OUTLINED)
        color = self.c["red"] if s.get("days_rest", 0) > 0 else self.c["amber"]
        detail = (f"{s['days_rest']} días de reposo"
                  if s.get("days_rest") else f"{s.get('races_banned',0)} carreras suspendido")

        return ft.Container(
            content=ft.Row([
                ft.Icon(icon, color=color, size=20),
                ft.Column([
                    ft.Text(s.get("reason", "Sanción"), size=12,
                            weight=ft.FontWeight.W_500, color=self.c["text"]),
                    ft.Text(detail, size=11, color=color),
                ], expand=True, spacing=2),
            ], spacing=10),
            bgcolor=self.c["surface"],
            border_radius=8,
            border=ft.border.all(0.5, color + "44"),
            padding=12,
        )

    def _recovery_option(self, name, desc, price) -> ft.Container:
        return ft.Container(
            content=ft.Column([
                ft.Text(name, size=11, weight=ft.FontWeight.W_500, color=self.c["text"]),
                ft.Text(desc, size=10, color=self.c["muted"]),
                ft.Text(f"${price:,}", size=11, color=self.c["amber"],
                        weight=ft.FontWeight.W_500),
            ], spacing=3),
            bgcolor=self.c["surface2"],
            border_radius=6,
            border=ft.border.all(0.5, self.c["border"]),
            padding=10,
            expand=True,
        )
