# core/subs_manager.py
import os
import csv
import asyncio
from datetime import datetime, timezone
from dateutil.relativedelta import relativedelta
from core.database import db

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA_FOLDER = os.path.join(BASE_DIR, "data")
IMPORT_FILE = os.path.join(DATA_FOLDER, "imports", "subscriber-list.csv")

class SubsManager:
    def __init__(self, debug=True):
        self.db = db
        self.debug = debug

    # ----------------- SINCRONIZACIÓN AL INICIO -----------------
    def sync_inicio(self):
        """Método seguro para usar en arranque de la app"""
        try:
            asyncio.run(self.actualizar_desde_twitch())
        except Exception as e:
            if self.debug:
                print(f"❌ Error en sync_inicio: {e}")

    # ----------------- ACTUALIZAR DESDE TWITCH -----------------
    async def actualizar_desde_twitch(self):
        """
        Sincroniza los subs desde Twitch y actualiza la DB local.
        """
        try:
            # Import local para evitar circular import
            from core.twitch_manager import TwitchManager  

            manager = TwitchManager()
            exito = await manager.actualizar_subs_desde_api()
            if exito:
                self.importar_subs_al_arrancar()
            return exito
        except Exception as e:
            if self.debug:
                print(f"❌ Error en actualizar_desde_twitch: {e}")
            return False

    def calcular_meses_desde_fecha(self, fecha_str):
        """Calcula los meses desde una fecha de inicio hasta hoy"""
        try:
            if not fecha_str:
                return 1
            
            # Parsear la fecha
            if 'Z' in fecha_str:
                fecha_inicio = datetime.fromisoformat(fecha_str.replace('Z', '+00:00'))
            else:
                fecha_inicio = datetime.fromisoformat(fecha_str)
            
            ahora = datetime.now(timezone.utc)
            
            # Calcular diferencia en meses
            diferencia = relativedelta(ahora, fecha_inicio)
            meses = diferencia.years * 12 + diferencia.months
            
            # Si ya pasó el día del mes actual, contar el mes actual
            if ahora.day >= fecha_inicio.day:
                meses += 1
            
            # Mínimo 1 mes
            return max(1, meses)
            
        except Exception as e:
            if self.debug:
                print(f"⚠️ Error calculando meses desde {fecha_str}: {e}")
            return 1

    def obtener_meses_desde_csv(self, fila):
        """
        Obtiene los meses totales desde el CSV.
        Prioridad: Tenure > Cumulative Months > meses > calcular desde fecha
        """
        # Buscar el campo Tenure (meses totales de suscripción)
        tenure = fila.get("Tenure") or fila.get("Cumulative Months") or fila.get("meses")
        
        if tenure:
            try:
                meses = int(tenure)
                if self.debug:
                    print(f"📊 Usando campo Tenure: {meses} meses")
                return meses
            except (ValueError, TypeError):
                if self.debug:
                    print(f"⚠️ No se pudo convertir Tenure a número: {tenure}")
        
        # Si no hay Tenure, calcular desde la fecha
        fecha_str = fila.get("Subscribe Date")
        if fecha_str:
            if self.debug:
                print(f"📅 No hay Tenure, calculando desde fecha: {fecha_str}")
            return self.calcular_meses_desde_fecha(fecha_str)
        
        # Si todo falla, devolver 1 mes
        if self.debug:
            print(f"⚠️ No se pudo determinar meses, usando 1")
        return 1

    # ----------------- IMPORTAR SUBS DESDE CSV -----------------
    def importar_subs_al_arrancar(self):
        ahora = datetime.now(timezone.utc)

        if not os.path.exists(IMPORT_FILE):
            if self.debug:
                print(f"⚠️ No se encontró el CSV en: {IMPORT_FILE}")
            return

        try:
            with open(IMPORT_FILE, "r", encoding="utf-8") as f:
                reader = csv.DictReader(f)
                
                # Mostrar los campos disponibles para depuración
                if self.debug:
                    print(f"📋 Campos disponibles en CSV: {list(reader.fieldnames) if reader.fieldnames else 'No se pudieron leer'}")
                
                for fila in reader:
                    usuario = (fila.get("Username") or fila.get("user_name") or "").lower().strip()
                    if not usuario:
                        continue

                    fecha_str = fila.get("Subscribe Date")
                    tier_label = fila.get("Current Tier") or "Tier 1"
                    
                    # OBTENER MESES TOTALES (usa Tenure primero, luego fecha)
                    meses = self.obtener_meses_desde_csv(fila)
                    
                    try:
                        fecha_iso = fecha_str.replace("Z", "+00:00") if fecha_str else ahora.isoformat()
                        tier = 1
                        if "3" in str(tier_label): 
                            tier = 3
                        elif "2" in str(tier_label): 
                            tier = 2

                        # Guardar el suscriptor CON LOS MESES TOTALES
                        self.guardar_sub(
                            tipo='normal', 
                            tier=tier, 
                            usuario=usuario, 
                            meses=meses,  # Usar meses totales
                            fecha=fecha_iso
                        )
                        
                        if self.debug:
                            print(f"✨ Sub guardada/actualizada: {usuario} | Tier {tier} | Meses {meses}")

                    except Exception as e:
                        if self.debug:
                            print(f"❌ Error procesando fila para {usuario}: {e}")

            if self.debug:
                print("✅ IMPORTACIÓN FINALIZADA desde CSV.")

        except Exception as e:
            if self.debug:
                print(f"❌ Error leyendo el CSV: {e}")

    # ----------------- GUARDAR SUB -----------------
    def guardar_sub(self, tipo, tier, usuario=None, regalador=None, receptor=None, meses=1, fecha=None):
        """
        Guarda un suscriptor en la base de datos.
        Guarda los meses totales directamente sin acumular.
        """
        target = usuario if tipo == 'normal' else receptor
        if not target:
            if self.debug:
                print(f"⚠️ No se pudo guardar sub: target vacío")
            return

        # Obtener suscriptor existente (si existe)
        existente = self.db.get_subscriber(target.lower())
        
        # Si existe, comparar tier y actualizar al mayor
        if existente:
            tier_final = max(existente['tier'], tier)
            # Usar los meses nuevos (totales), NO sumar
            meses_final = meses
        else:
            tier_final = tier
            meses_final = meses

        # Guardar en base de datos
        fecha_iso = fecha or datetime.now(timezone.utc).isoformat()
        self.db.save_subscriber(
            target.lower(), 
            tier=tier_final, 
            meses=meses_final,  # Guardar los meses totales
            fecha=fecha_iso
        )
        

    # ----------------- ELIMINAR SUB -----------------
    def eliminar_sub(self, usuario):
        if not usuario:
            return
        self.db.delete_subscriber(usuario.lower())
        if self.debug:
            print(f"🗑️ Sub eliminada: {usuario.lower()}")