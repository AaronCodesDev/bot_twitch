# ui/colors.py
# Sistema de diseño unificado — FanTan Hub

import flet as ft

# ─── Paleta principal ─────────────────────────────────────────────────────────
BG          = "#08090f"       # Fondo profundo
SURFACE     = "#111420"       # Superficie base
SURFACE2    = "#181c2a"       # Superficie elevada
SURFACE3    = "#1f2438"       # Superficie más elevada (hover, activo)
BORDER      = "#ffffff0d"     # Borde sutil
BORDER2     = "#ffffff18"     # Borde visible

# ─── Acentos por módulo ───────────────────────────────────────────────────────
PURPLE      = "#9147ff"       # Twitch purple
PURPLE_L    = "#b880ff"       # Twitch purple claro
ORANGE      = "#f97316"       # iRacing orange
ORANGE_L    = "#fb923c"       # iRacing orange claro
GREEN       = "#22c55e"       # Career green
GREEN_L     = "#4ade80"       # Career green claro
CYAN        = "#06b6d4"       # Accent general

# ─── Semánticos ───────────────────────────────────────────────────────────────
SUCCESS     = "#22c55e"
WARNING     = "#f59e0b"
DANGER      = "#ef4444"
INFO        = "#3b82f6"

# ─── Texto ────────────────────────────────────────────────────────────────────
TEXT        = "#e8e6f0"
MUTED       = "#7c7a8e"
MUTED2      = "#5a5870"

# ─── Helpers ──────────────────────────────────────────────────────────────────
def with_alpha(hex_color: str, alpha: float) -> str:
    """Añade transparencia a un color hex (alpha 0.0–1.0)."""
    r = int(hex_color[1:3], 16)
    g = int(hex_color[3:5], 16)
    b = int(hex_color[5:7], 16)
    a = int(alpha * 255)
    return f"#{a:02x}{r:02x}{g:02x}{b:02x}"

# ─── Dict unificado para pasar a vistas ───────────────────────────────────────
COLORS = {
    "bg": BG,
    "surface": SURFACE,
    "surface2": SURFACE2,
    "surface3": SURFACE3,
    "border": BORDER,
    "border2": BORDER2,
    "purple": PURPLE,
    "purple_l": PURPLE_L,
    "orange": ORANGE,
    "orange_l": ORANGE_L,
    "green": GREEN,
    "green_l": GREEN_L,
    "cyan": CYAN,
    "success": SUCCESS,
    "warning": WARNING,
    "danger": DANGER,
    "info": INFO,
    "text": TEXT,
    "muted": MUTED,
    "muted2": MUTED2,
}

# Accents por módulo
MODULE_ACCENT = {
    "home":    CYAN,
    "twitch":  PURPLE,
    "tracker": ORANGE,
    "career":  GREEN,
}
