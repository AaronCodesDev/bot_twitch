import flet as ft

class AppColors:
    # Generales
    BG_DARK = "#0d0d0d"
    SURFACE = "#121212"
    ACCENT = ft.Colors.BLUE_700
    
    # Tiers de Twitch
    T3_COLOR = ft.Colors.PURPLE_ACCENT_100
    T3_BG = "#2b0040"
    T2_COLOR = ft.Colors.BLUE_400
    T2_BG = "#001a33"
    T1_COLOR = ft.Colors.GREEN_400
    T1_BG = "#0d1a0d"

class AppStyles:
    # Estilo para los contenedores de los mensajes (Terminal/Chat)
    BOX_CONTAINER = {
        "expand": True,
        "bgcolor": AppColors.BG_DARK,
        "padding": 10,
        "border_radius": 10,
        "border": ft.border.all(1, ft.Colors.GREY_900)
    }
    
    # Estilo para las tarjetas de suscriptores
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
            "border_radius": 10,
            "border": ft.border.all(1, "#333333"),
            "margin": ft.margin.only(top=5)
        }