import os
import csv
from datetime import datetime, timezone
from core.persistence import cargar_json, guardar_json, cargar_suscriptores
from core.memory import Memory
from core.twitch_manager import TwitchManager  # <--- IMPORTANTE: Añadir este import

# Configuración de rutas
DATA_FOLDER = 'data'
SUBS_MES_DIR = os.path.join(DATA_FOLDER, 'subs/')
IMPORT_FILE = os.path.join(DATA_FOLDER, 'imports/subscriber-list.csv')
CUENTA_PROPIA = 'fantan'

class SubsManager:

    @staticmethod
    async def actualizar_desde_twitch():
        """Llama al TwitchManager para descargar el CSV actualizado de la API."""
        try:
            # Instanciamos el manager de Twitch
            manager = TwitchManager()
            # Intentamos la descarga
            exito = await manager.actualizar_csv_desde_twitch()
            if exito:
                print("✅ CSV actualizado correctamente desde Twitch API.")
            return exito
        except Exception as e:
            print(f"❌ Error crítico en SubsManager.actualizar_desde_twitch: {e}")
            return False

    @staticmethod
    def guardar_sub(tipo, tier, usuario=None, regalador=None, receptor=None, blindado=True):
        ahora = datetime.now()
        mes = ahora.strftime("%Y-%m")
        fecha = ahora.strftime('%Y-%m-%d')
        archivo = os.path.join(SUBS_MES_DIR, f"subs_{mes}.json")
        
        datos = cargar_json(archivo, {'normal': {}, 'regaladas': []})

        # --- Lógica de guardado histórico ---
        if tipo == 'normal' and usuario:
            if not blindado or usuario not in datos['normal']:
                datos['normal'][usuario] = datos['normal'].get(usuario, 0) + 1
        elif tipo == 'regalada' and regalador and receptor:
            if not any(r['regalador']==regalador and r['receptor']==receptor and r['tier']==tier for r in datos['regaladas']):
                datos['regaladas'].append({'regalador': regalador, 'receptor': receptor, 'tier': tier, 'fecha': fecha})

        guardar_json(archivo, datos)

        # --- Actualizar subs activos ---
        subs_activos = cargar_suscriptores()
        target = usuario if tipo == 'normal' else receptor
        if target:
            # Solo actualiza si es nuevo o la fecha registrada es anterior
            if target not in subs_activos or datetime.fromisoformat(subs_activos[target]["fecha"]).replace(tzinfo=None) < ahora:
                subs_activos[target] = {'fecha': ahora.isoformat(), 'tier': tier}
                guardar_json(os.path.join(DATA_FOLDER, 'subs/subscriptores_activos.json'), subs_activos)

    @staticmethod
    def importar_subs_al_arrancar(blindado=True):
        """Importa el CSV de Twitch y limpia expirados."""
        ahora = datetime.now(timezone.utc)
        
        # Asegurar archivo del mes actual
        archivo_mes_actual = os.path.join(SUBS_MES_DIR, f"subs_{ahora.strftime('%Y-%m')}.json")
        if not os.path.exists(archivo_mes_actual):
            guardar_json(archivo_mes_actual, {"normal": {}, "regaladas": []})

        if not os.path.exists(IMPORT_FILE):
            print("⚠️ No hay CSV para importar.")
            return

        print("🔄 Importando subs desde CSV...")
        activos_actualizados = {}

        with open(IMPORT_FILE, "r", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            headers = reader.fieldnames or []
            
            for fila in reader:
                usuario = (fila.get("Username") or fila.get("user_name", "")).lower()
                if not usuario or usuario == CUENTA_PROPIA: continue

                fecha_str = fila.get("Subscribe Date") or fila.get("created_at")
                tier_raw = fila.get("Current Tier") or fila.get("tier", 1000)

                try:
                    fecha_dt = datetime.fromisoformat(fecha_str.replace("Z", "+00:00"))
                    if (ahora - fecha_dt).days <= Memory.SUB_DURATION_DAYS:
                        tier = int(str(tier_raw).replace("Tier ", "")) if "Tier" in str(tier_raw) else int(tier_raw)//1000
                        activos_actualizados[usuario] = {"fecha": fecha_dt.isoformat(), "tier": tier}
                        
                        # Guardar en histórico mensual
                        mes_llave = fecha_dt.strftime("%Y-%m")
                        archivo_h = os.path.join(SUBS_MES_DIR, f"subs_{mes_llave}.json")
                        h_datos = cargar_json(archivo_h, {"normal": {}, "regaladas": []})
                        if usuario not in h_datos["normal"]: h_datos["normal"][usuario] = 1
                        guardar_json(archivo_h, h_datos)
                except: continue

        guardar_json(os.path.join(DATA_FOLDER, 'subs/subscriptores_activos.json'), activos_actualizados)
        print("✅ Importación y limpieza de activos completada.")