# core/persistence.py
from core.database import db

def cargar_suscriptores():
    subs = db.get_all_subscribers()
    return {s["username"]: s for s in subs}

def cargar_favoritos():
    favoritos = db.get_all_favoritos()
    return {f["nombre"]: f["contenido"] for f in favoritos}

def cargar_ideas():
    return db.get_all_ideas()

def es_canal_pro(channel_name: str) -> bool:
    sub = db.get_subscriber(channel_name.lower())
    return sub is not None and sub.get("tier", 1) >= 2