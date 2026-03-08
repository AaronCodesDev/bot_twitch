import os
import csv
from datetime import datetime, timezone
from core.persistence import (
    cargar_json, guardar_json, cargar_suscriptores, 
    SUBS_FILE, DATA_FOLDER
)
from core.memory import Memory
from core.twitch_manager import TwitchManager

# Configuración de rutas
IMPORT_FILE = os.path.join(DATA_FOLDER, 'imports', 'subscriber-list.csv')

class SubsManager:

    @staticmethod
    async def actualizar_desde_twitch():
        """Llama al TwitchManager para descargar el CSV actualizado."""
        try:
            manager = TwitchManager()
            exito = await manager.actualizar_csv_desde_twitch()
            if exito:
                SubsManager.importar_subs_al_arrancar()
            return exito
        except Exception as e:
            print(f"❌ Error en SubsManager.actualizar_desde_twitch: {e}")
            return False

    @staticmethod
    def importar_subs_al_arrancar():
        """Lee el CSV y procesa los suscriptores (INCLUYENDO AL STREAMER PARA PRUEBAS)."""
        ahora = datetime.now(timezone.utc)
        
        if not os.path.exists(IMPORT_FILE):
            print(f"⚠️ No se encontró el CSV en: {IMPORT_FILE}")
            return

        activos_actualizados = {}

        try:
            with open(IMPORT_FILE, "r", encoding="utf-8") as f:
                reader = csv.DictReader(f)
                
                for fila in reader:
                    # Buscamos el nombre de usuario de forma flexible
                    usuario = (fila.get("Username") or fila.get("user_name") or "").lower().strip()
                    
                    # --- REGLA DE PRUEBA ---
                    # Hemos quitado el filtro 'usuario == CUENTA_PROPIA' 
                    # para que 'fantan' SÍ sea contado como suscriptor.
                    if not usuario: 
                        continue

                    fecha_str = fila.get("Subscribe Date")
                    tier_label = fila.get("Current Tier", "Tier 1")

                    try:
                        # Si hay fecha la usamos, si no, ponemos la de ahora
                        fecha_iso = fecha_str.replace("Z", "+00:00") if fecha_str else ahora.isoformat()
                        
                        # Mapeo de Tier
                        tier = 1
                        if "3" in str(tier_label): tier = 3
                        elif "2" in str(tier_label): tier = 2
                        
                        activos_actualizados[usuario] = {
                            "fecha": fecha_iso, 
                            "tier": tier
                        }
                    except:
                        activos_actualizados[usuario] = {"fecha": ahora.isoformat(), "tier": 1}

            # Guardamos el JSON que lee el bot
            guardar_json(SUBS_FILE, activos_actualizados)
            print(f"✅ IMPORTACIÓN EXITOSA: {len(activos_actualizados)} subs activos detectados.")

        except Exception as e:
            print(f"❌ Error leyendo el CSV: {e}")

    @staticmethod
    def guardar_sub(tipo, tier, usuario=None, regalador=None, receptor=None):
        """Guarda subs en vivo."""
        ahora = datetime.now(timezone.utc)
        subs_activos = cargar_suscriptores()
        target = (usuario if tipo == 'normal' else receptor).lower()
        if target:
            try:
                t_val = int(tier)
                tier_num = t_val // 1000 if t_val >= 1000 else t_val
            except: tier_num = 1
            subs_activos[target] = {'fecha': ahora.isoformat(), 'tier': tier_num}
            guardar_json(SUBS_FILE, subs_activos)
            print(f"✨ Sub en vivo guardada: {target}")