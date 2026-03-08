import json
import os

# --- RUTAS DE ARCHIVOS (CORREGIDO PARA ESTRUCTURA CON /core) ---
# __file__ es persistence.py
# dirname(__file__) es la carpeta 'core'
# dirname(dirname(__file__)) es la raíz del bot 'bot'
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# Si ves que sigue fallando, vamos a forzar la carpeta 'data' de forma más simple:
DATA_FOLDER = os.path.join(BASE_DIR, 'data')

# RUTAS EXACTAS
FAVORITOS_FILE = os.path.join(DATA_FOLDER, 'save', 'favoritos.json')
SUBS_FILE = os.path.join(DATA_FOLDER, 'subs', 'subscriptores_activos.json')
IDEAS_FILE = os.path.join(DATA_FOLDER, 'save', 'ideas_sorteo.json')

def cargar_json(ruta, default=None):
    if default is None: default = {}
    if os.path.exists(ruta):
        try:
            with open(ruta, 'r', encoding='utf-8') as f:
                data = json.load(f)
                # Forzamos que las llaves sean minúsculas para evitar errores de Fantan vs fantan
                if isinstance(data, dict):
                    return {k.lower(): v for k, v in data.items()}
                return data
        except json.JSONDecodeError:
            print(f"⚠️ Error: El archivo {ruta} está corrupto.")
            return default
    else:
        print(f"⚠️ Archivo no encontrado: {ruta}")
    return default

def guardar_json(ruta, datos):
    os.makedirs(os.path.dirname(ruta), exist_ok=True)
    with open(ruta, 'w', encoding='utf-8') as f:
        json.dump(datos, f, indent=4, ensure_ascii=False)

# --- CARGADORES ESPECÍFICOS ---
def cargar_favoritos(): return cargar_json(FAVORITOS_FILE, {})
def cargar_suscriptores(): return cargar_json(SUBS_FILE, {})
def cargar_ideas(): return cargar_json(IDEAS_FILE, [])