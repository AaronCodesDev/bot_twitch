import json
import os

# --- RUTAS DE ARCHIVOS ---
DATA_FOLDER = 'data'
FAVORITOS_FILE = os.path.join(DATA_FOLDER, 'save/favoritos.json')
SUBS_FILE = os.path.join(DATA_FOLDER, 'subs/subscriptores_activos.json')
IDEAS_FILE = os.path.join(DATA_FOLDER, 'save/ideas_sorteo.json')

def cargar_json(ruta, default=None):
    if default is None: default = {}
    if os.path.exists(ruta):
        try:
            with open(ruta, 'r', encoding='utf-8') as f:
                return json.load(f)
        except json.JSONDecodeError:
            return default
    return default

def guardar_json(ruta, datos):
    os.makedirs(os.path.dirname(ruta), exist_ok=True)
    with open(ruta, 'w', encoding='utf-8') as f:
        json.dump(datos, f, indent=4, ensure_ascii=False)

# --- CARGADORES ESPECÍFICOS ---
def cargar_favoritos(): return cargar_json(FAVORITOS_FILE, {})
def cargar_suscriptores(): return cargar_json(SUBS_FILE, {})
def cargar_ideas(): return cargar_json(IDEAS_FILE, [])