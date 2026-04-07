import flet as ft

SHOP_ITEMS = [
    {"id": "piso",     "name": "Piso básico",       "category": "Inmuebles", "price": 12000,  "icon": ft.Icons.HOME_OUTLINED},
    {"id": "chalet",   "name": "Chalet piloto",     "category": "Inmuebles", "price": 85000,  "icon": ft.Icons.VILLA_OUTLINED},
    {"id": "mansion",  "name": "Mansión campeón",   "category": "Inmuebles", "price": 320000, "icon": ft.Icons.APARTMENT_OUTLINED, "min_wins": 20},
    {"id": "coche",    "name": "Coche normal",      "category": "Vehículos", "price": 8000,   "icon": ft.Icons.DIRECTIONS_CAR_OUTLINED},
    {"id": "super",    "name": "Superdeportivo",    "category": "Vehículos", "price": 45000,  "icon": ft.Icons.SPEED_OUTLINED},
    {"id": "yate",     "name": "Yate privado",      "category": "Vehículos", "price": 180000, "icon": ft.Icons.SAILING_OUTLINED, "min_wins": 15},
    {"id": "jet",      "name": "Jet privado",       "category": "Extras",   "price": 500000, "icon": ft.Icons.FLIGHT_OUTLINED,  "min_wins": 30},
    {"id": "reloj",    "name": "Reloj de lujo",     "category": "Extras",   "price": 9500,   "icon": ft.Icons.WATCH_OUTLINED},
]


class ShopView:
    def __init__(self, data, colors, engine):
        self.data = data or {}
        self.c = colors
        self.engine = engine

    def build(self) -> ft.Control:
        pilot = self.data.get("pilot", {})
        balance = pilot.get("balance", 0)
        races = self.data.get("recent_races", [])
        wins = sum(1 for r in races if r.get("finish_position") == 1)

        categories = {}
        for item in SHOP_ITEMS:
            categories.setdefault(item["category"], []).append(item)

        sections = []
        for cat, items in categories.items():
            grid = ft.Row(
                [self._item_card(i, balance, wins) for i in items],
                wrap=True, spacing=8,
            )
            sections.append(ft.Column([
                ft.Text(cat.upper(), size=10, color=self.c["muted"],
                        weight=ft.FontWeight.W_500),
                grid,
            ], spacing=6))

        return ft.Column(
            [
                ft.Container(
                    content=ft.Row([
                        ft.Icon(ft.Icons.ACCOUNT_BALANCE_WALLET_OUTLINED,
                                color=self.c["green"], size=16),
                        ft.Text(f"Balance disponible: ${balance:,.0f}",
                                size=12, color=self.c["green"],
                                weight=ft.FontWeight.W_500),
                    ], spacing=6),
                    bgcolor=self.c["surface"],
                    border_radius=8,
                    border=ft.border.all(0.5, self.c["green"] + "44"),
                    padding=10,
                ),
                *sections,
            ],
            spacing=14, scroll=ft.ScrollMode.AUTO,
        )

    def _item_card(self, item, balance, wins) -> ft.Container:
        locked = item.get("min_wins", 0) > wins
        can_buy = not locked and balance >= item["price"]
        color = (self.c["muted"] if locked
                 else self.c["green"] if can_buy
                 else self.c["red"])
        label = "Bloqueado" if locked else ("Comprar" if can_buy else "Sin fondos")

        return ft.Container(
            content=ft.Column([
                ft.Icon(item["icon"], color=color, size=24),
                ft.Text(item["name"], size=11, weight=ft.FontWeight.W_500,
                        color=self.c["text"], text_align=ft.TextAlign.CENTER),
                ft.Text(f"${item['price']:,}", size=10, color=color,
                        text_align=ft.TextAlign.CENTER),
                ft.Container(
                    content=ft.Text(label, size=9, color=color),
                    bgcolor=color + "18",
                    border=ft.border.all(0.5, color + "44"),
                    border_radius=6,
                    padding=ft.padding.symmetric(horizontal=8, vertical=2),
                ),
            ], spacing=4, horizontal_alignment=ft.CrossAxisAlignment.CENTER),
            bgcolor=self.c["surface"],
            border_radius=8,
            border=ft.border.all(0.5, self.c["border"]),
            padding=12,
            width=130,
        )
