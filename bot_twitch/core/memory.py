# core/memory.py
from core.database import db
from datetime import datetime

class Memory:

    def __init__(self, debug=True):
        self.debug = debug
        if self.debug:
            print("🔥 Sistema de memoria listo.")

    # ------------------ Hechos ------------------
    def add_hecho(self, sujeto, accion, lugar=None, contexto=None, autor=None):
        db.add_hecho(
            sujeto=sujeto.lower(),
            accion=accion.lower(),
            lugar=lugar.lower() if lugar else None,
            contexto=contexto,
            autor=autor
        )

    def buscar_hechos(self, sujeto):
        return db.get_hechos(sujeto.lower())

    # ------------------ Usuarios ------------------
    def ensure_user(self, user: str):
        db.ensure_user_profile(user.lower())

    # ------------------ Frases (!soy) ------------------
    def add_frase(self, user: str, frase: str, confianza: int = 1):
        db.add_frase(user.lower(), frase, confianza)

    def get_frases(self, user: str):
        return db.get_frases(user.lower())

    # ------------------ Recuerdos ------------------
    def add_recuerdo(self, user: str, texto: str):
        texto = texto.strip()
        for char in ["\u200b", "\u200c", "\u200d", "\u2060", "͏"]:
            texto = texto.replace(char, "")
        if not texto:
            return
        db.add_recuerdo(user.lower(), texto)

    def get_recuerdos(self, user: str, max_items: int = 5):
        return db.get_recuerdos(user.lower(), max_items)

    # ------------------ Confianza ------------------
    def add_confianza(self, user: str, valor: int):
        db.add_confianza(user.lower(), valor)

    def get_confianza(self, user: str) -> int:
        return db.get_confianza(user.lower())

    # ------------------ Favoritos ------------------
    def get_favorito(self, nombre: str):
        return db.get_favorito(nombre.lower())

    def save_favorito(self, nombre: str, contenido: str):
        db.save_favorito(nombre.lower(), contenido)

    def get_all_favoritos(self):
        return db.get_all_favoritos()

    # ------------------ Suscriptores ------------------
    def save_subscriber(self, username: str, tier: int = 1, meses: int = 1):
        db.save_subscriber(username.lower(), tier, meses)

    def get_subscriber(self, username: str):
        return db.get_subscriber(username.lower())

    def get_all_subscribers(self):
        return db.get_all_subscribers()

    # ------------------ Subs mensuales ------------------
    def add_monthly_sub_normal(self, user: str, months: int = 1,
                                dt: datetime = None) -> bool:
        dt = dt or datetime.now()
        return db.add_sub_mensual_normal(
            username=user.lower(),
            meses=months,
            year=dt.year,
            month=dt.month
        )

    def add_monthly_sub_gift(self, gifter: str, receiver: str,
                              dt: datetime = None) -> bool:
        dt = dt or datetime.now()
        return db.add_sub_mensual_regalo(
            gifter=gifter.lower(),
            receiver=receiver.lower(),
            year=dt.year,
            month=dt.month
        )

    def get_draw_pool(self, year: int, month: int):
        return db.get_draw_pool(year, month)