import flet as ft

class AppColors:
    # Generales (Base)
    BG_DARK = "#0d0d0d"
    SURFACE = "#121212"
    ACCENT = ft.Colors.BLUE_700
    PRIMARY = ft.Colors.BLUE_700
    
    # Colores Glassmorphism (Nuevos)
    GLASS_BG = ft.Colors.with_opacity(0.1, "white")
    GLASS_BORDER = "white10"
    
    # Tiers de Twitch
    T3_COLOR = ft.Colors.PURPLE_ACCENT_100
    T3_BG = ft.Colors.with_opacity(0.2, "purple") # Glass para Tiers
    T2_COLOR = ft.Colors.BLUE_400
    T2_BG = ft.Colors.with_opacity(0.2, "blue")
    T1_COLOR = ft.Colors.GREEN_400
    T1_BG = ft.Colors.with_opacity(0.2, "green")

class AppStyles:
    # Estilo Glassmorphism para Terminal/Chat
    BOX_CONTAINER = {
        "expand": True,
        "bgcolor": AppColors.GLASS_BG,
        "padding": 15,
        "border_radius": 20,
        "border": ft.border.all(1, AppColors.GLASS_BORDER),
        "blur": ft.Blur(20, 20), # <--- Aquí sucede la magia
    }
    
    # Estilo para las tarjetas de suscriptores (Ahora con toque Glass)
    @staticmethod
    def sub_card(tier):
        colors = {
            3: (AppColors.T3_COLOR, AppColors.T3_BG),
            2: (AppColors.T2_COLOR, AppColors.T2_BG),
            1: (AppColors.T1_COLOR, AppColors.T1_BG)
        }
        c, bg = colors.get(tier, colors[1])
        return {
            "padding": 10,
            "bgcolor": bg,
            "border_radius": 15,
            "border": ft.border.all(1, "white10"),
            "blur": ft.Blur(5, 5), # Desenfoque más suave para cards pequeñas
            "margin": ft.margin.only(top=5)
        }