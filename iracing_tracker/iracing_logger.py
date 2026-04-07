#!/usr/bin/env python3
"""
iRacing Telemetry Logger v2
Captura datos en tiempo real con pyiRSDK + estadísticas oficiales con iracing_garage.
Optimizado para categorías Road (GT3, LMP, F1, etc.)
"""

import irsdk
import time
import sqlite3
import os
from datetime import datetime
from pathlib import Path
from dotenv import load_dotenv

# Cargar credenciales
load_dotenv()

# Configuración
DB_PATH = Path(__file__).parent / "iracing_data.db"
POLL_RATE = 1  # Segundos entre cada lectura


def init_database():
    """Crea las tablas si no existen."""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    # Tabla de perfil del piloto (histórico de iRating/SR)
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS driver_profile (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            cust_id INTEGER,
            display_name TEXT,
            irating_road INTEGER,
            irating_oval INTEGER,
            irating_dirt_road INTEGER,
            irating_dirt_oval INTEGER,
            sr_road REAL,
            sr_oval REAL,
            sr_dirt_road REAL,
            sr_dirt_oval REAL,
            license_road TEXT,
            license_oval TEXT,
            laps_road INTEGER,
            wins_road INTEGER,
            top5_road INTEGER,
            starts_road INTEGER
        )
    """)
    
    # Tabla de sesiones
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS sessions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            session_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            subsession_id INTEGER,
            track_name TEXT,
            track_config TEXT,
            car_name TEXT,
            car_id INTEGER,
            session_type TEXT,
            series_name TEXT,
            sof INTEGER,
            start_position INTEGER,
            finish_position INTEGER,
            total_laps INTEGER,
            total_incidents INTEGER,
            best_lap_time REAL,
            avg_lap_time REAL,
            irating_before INTEGER,
            irating_after INTEGER,
            irating_change INTEGER,
            sr_before REAL,
            sr_after REAL,
            sr_change REAL,
            champ_points INTEGER,
            notes TEXT
        )
    """)
    
    # Tabla de vueltas
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS laps (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            session_id INTEGER,
            lap_number INTEGER,
            lap_time REAL,
            sector1 REAL,
            sector2 REAL,
            sector3 REAL,
            position INTEGER,
            gap_ahead REAL,
            gap_behind REAL,
            incidents_this_lap INTEGER,
            fuel_used REAL,
            fuel_remaining REAL,
            tire_wear_fl REAL,
            tire_wear_fr REAL,
            tire_wear_rl REAL,
            tire_wear_rr REAL,
            max_speed REAL,
            is_valid INTEGER DEFAULT 1,
            pit_stop INTEGER DEFAULT 0,
            FOREIGN KEY (session_id) REFERENCES sessions(id)
        )
    """)
    
    # Tabla de telemetría detallada
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS telemetry (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            session_id INTEGER,
            lap_number INTEGER,
            timestamp REAL,
            speed REAL,
            rpm REAL,
            gear INTEGER,
            throttle REAL,
            brake REAL,
            steering REAL,
            lat_accel REAL,
            long_accel REAL,
            track_position REAL,
            FOREIGN KEY (session_id) REFERENCES sessions(id)
        )
    """)
    
    # Tabla de resultados oficiales (de la API)
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS official_results (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            subsession_id INTEGER UNIQUE,
            session_id INTEGER,
            fetched_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            raw_json TEXT,
            FOREIGN KEY (session_id) REFERENCES sessions(id)
        )
    """)
    
    conn.commit()
    return conn


class iRacingAPI:
    """Wrapper para iracing_garage."""
    
    def __init__(self):
        self.client = None
        self.cust_id = os.getenv('IRACING_CUST_ID')
        self.connected = False
    
    def connect(self):
        """Conecta a la API de iRacing."""
        email = os.getenv('IRACING_EMAIL')
        password = os.getenv('IRACING_PASSWORD')
        
        if not email or not password:
            print("⚠️  Credenciales no configuradas en .env")
            print("   El tracking de iRating/SR no estará disponible")
            return False
        
        try:
            from iracing_garage import iRacingGarage
            self.client = iRacingGarage(email, password)
            self.connected = True
            print("✅ Conectado a iRacing API")
            return True
        except Exception as e:
            print(f"⚠️  Error conectando a API: {e}")
            return False
    
    def get_driver_stats(self):
        """Obtiene estadísticas actuales del piloto."""
        if not self.connected or not self.cust_id:
            return None
        
        try:
            stats = self.client.stats.summary(int(self.cust_id))
            return stats
        except Exception as e:
            print(f"⚠️  Error obteniendo stats: {e}")
            return None
    
    def get_recent_races(self, limit=10):
        """Obtiene carreras recientes."""
        if not self.connected or not self.cust_id:
            return None
        
        try:
            # Buscar resultados recientes del piloto
            results = self.client.results.search_hosted(
                cust_id=int(self.cust_id)
            )
            return results
        except Exception as e:
            print(f"⚠️  Error obteniendo carreras: {e}")
            return None
    
    def get_race_result(self, subsession_id):
        """Obtiene resultado detallado de una carrera."""
        if not self.connected:
            return None
        
        try:
            result = self.client.results.get(subsession_id, 0)
            return result
        except Exception as e:
            print(f"⚠️  Error obteniendo resultado: {e}")
            return None


class iRacingLogger:
    def __init__(self):
        self.ir = irsdk.IRSDK()
        self.api = iRacingAPI()
        self.conn = init_database()
        self.session_id = None
        self.subsession_id = None
        self.current_lap = 0
        self.lap_start_time = None
        self.session_incidents = 0
        self.lap_times = []
        self.is_connected = False
        self.irating_before = None
        self.sr_before = None
        
    def connect(self):
        """Conecta con iRacing."""
        if self.ir.startup():
            self.is_connected = True
            print("✅ Conectado a iRacing (sim)!")
            return True
        return False
    
    def disconnect(self):
        """Desconecta de iRacing."""
        self.ir.shutdown()
        self.is_connected = False
        print("🔌 Desconectado de iRacing")
    
    def save_driver_snapshot(self):
        """Guarda snapshot actual del perfil del piloto."""
        stats = self.api.get_driver_stats()
        if not stats:
            return
        
        cursor = self.conn.cursor()
        
        try:
            # Extraer datos relevantes (la estructura puede variar)
            cursor.execute("""
                INSERT INTO driver_profile (
                    cust_id, display_name,
                    irating_road, sr_road, license_road,
                    laps_road, wins_road, starts_road
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                self.api.cust_id,
                stats.get('display_name', 'Unknown'),
                stats.get('road', {}).get('irating', 0),
                stats.get('road', {}).get('sr', 0),
                stats.get('road', {}).get('license', 'R'),
                stats.get('road', {}).get('laps', 0),
                stats.get('road', {}).get('wins', 0),
                stats.get('road', {}).get('starts', 0)
            ))
            self.conn.commit()
            
            # Guardar para comparar después
            self.irating_before = stats.get('road', {}).get('irating', 0)
            self.sr_before = stats.get('road', {}).get('sr', 0)
            
            print(f"📊 iRating: {self.irating_before} | SR: {self.sr_before}")
            
        except Exception as e:
            print(f"⚠️  Error guardando snapshot: {e}")
    
    def start_session(self):
        """Inicia una nueva sesión de registro."""
        track_name = self.ir['WeekendInfo']['TrackDisplayName']
        track_config = self.ir['WeekendInfo']['TrackConfigName'] or 'Full'
        car_name = self.ir['DriverInfo']['Drivers'][self.ir['PlayerCarIdx']]['CarScreenName']
        car_id = self.ir['DriverInfo']['Drivers'][self.ir['PlayerCarIdx']]['CarID']
        session_type = self.ir['SessionInfo']['Sessions'][self.ir['SessionNum']]['SessionType']
        
        # Intentar obtener subsession_id
        try:
            self.subsession_id = self.ir['WeekendInfo']['SubSessionID']
        except:
            self.subsession_id = None
        
        # Obtener SOF si es carrera oficial
        sof = None
        try:
            sof = self.ir['WeekendInfo']['WeekendOptions'].get('SOF', None)
        except:
            pass
        
        cursor = self.conn.cursor()
        cursor.execute("""
            INSERT INTO sessions (
                track_name, track_config, car_name, car_id, 
                session_type, subsession_id, sof,
                irating_before, sr_before
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            track_name, track_config, car_name, car_id,
            session_type, self.subsession_id, sof,
            self.irating_before, self.sr_before
        ))
        self.conn.commit()
        self.session_id = cursor.lastrowid
        
        print(f"\n🏁 Nueva sesión iniciada:")
        print(f"   Pista: {track_name} ({track_config})")
        print(f"   Coche: {car_name}")
        print(f"   Tipo: {session_type}")
        if sof:
            print(f"   SOF: {sof}")
        print(f"   Session ID: {self.session_id}")
        print("-" * 50)
        
        return self.session_id
    
    def log_lap(self, lap_number, lap_time):
        """Registra los datos de una vuelta completada."""
        cursor = self.conn.cursor()
        
        position = self.ir['PlayerCarPosition']
        fuel = self.ir['FuelLevel']
        incidents = self.ir['PlayerCarMyIncidentCount']
        incidents_this_lap = incidents - self.session_incidents
        self.session_incidents = incidents
        
        pit_stop = 1 if self.ir['OnPitRoad'] else 0
        
        cursor.execute("""
            INSERT INTO laps (
                session_id, lap_number, lap_time, position,
                incidents_this_lap, fuel_remaining, pit_stop
            ) VALUES (?, ?, ?, ?, ?, ?, ?)
        """, (self.session_id, lap_number, lap_time, position,
              incidents_this_lap, fuel, pit_stop))
        self.conn.commit()
        
        self.lap_times.append(lap_time)
        
        incident_str = f" ⚠️ +{incidents_this_lap}x" if incidents_this_lap > 0 else ""
        print(f"   Vuelta {lap_number:3d}: {self.format_time(lap_time)}  P{position}{incident_str}")
    
    def log_telemetry(self, lap_number):
        """Registra telemetría del momento actual."""
        cursor = self.conn.cursor()
        
        cursor.execute("""
            INSERT INTO telemetry (
                session_id, lap_number, timestamp, speed, rpm, gear,
                throttle, brake, steering, lat_accel, long_accel, track_position
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            self.session_id,
            lap_number,
            time.time(),
            self.ir['Speed'] * 3.6,
            self.ir['RPM'],
            self.ir['Gear'],
            self.ir['Throttle'] * 100,
            self.ir['Brake'] * 100,
            self.ir['SteeringWheelAngle'],
            self.ir['LatAccel'],
            self.ir['LongAccel'],
            self.ir['LapDistPct']
        ))
        self.conn.commit()
    
    def fetch_official_results(self):
        """Obtiene resultados oficiales después de la carrera."""
        if not self.subsession_id:
            print("   No hay subsession_id, saltando resultados oficiales")
            return
        
        print("\n⏳ Esperando resultados oficiales (30s)...")
        time.sleep(30)  # Esperar a que iRacing procese
        
        result = self.api.get_race_result(self.subsession_id)
        if not result:
            print("   No se pudieron obtener resultados oficiales")
            return
        
        # Guardar JSON completo
        import json
        cursor = self.conn.cursor()
        cursor.execute("""
            INSERT OR REPLACE INTO official_results (subsession_id, session_id, raw_json)
            VALUES (?, ?, ?)
        """, (self.subsession_id, self.session_id, json.dumps(result)))
        self.conn.commit()
        
        print("✅ Resultados oficiales guardados")
    
    def update_post_race_stats(self):
        """Actualiza estadísticas después de la carrera."""
        stats = self.api.get_driver_stats()
        if not stats:
            return
        
        irating_after = stats.get('road', {}).get('irating', 0)
        sr_after = stats.get('road', {}).get('sr', 0)
        
        irating_change = irating_after - (self.irating_before or 0)
        sr_change = sr_after - (self.sr_before or 0)
        
        cursor = self.conn.cursor()
        cursor.execute("""
            UPDATE sessions SET
                irating_after = ?,
                sr_after = ?,
                irating_change = ?,
                sr_change = ?
            WHERE id = ?
        """, (irating_after, sr_after, irating_change, sr_change, self.session_id))
        self.conn.commit()
        
        # Mostrar cambios
        ir_symbol = "📈" if irating_change >= 0 else "📉"
        sr_symbol = "📈" if sr_change >= 0 else "📉"
        
        print(f"\n{ir_symbol} iRating: {self.irating_before} → {irating_after} ({irating_change:+d})")
        print(f"{sr_symbol} SR: {self.sr_before:.2f} → {sr_after:.2f} ({sr_change:+.2f})")
    
    def finish_session(self):
        """Finaliza la sesión y calcula estadísticas."""
        if not self.session_id or not self.lap_times:
            return
        
        cursor = self.conn.cursor()
        
        best_lap = min(self.lap_times) if self.lap_times else 0
        avg_lap = sum(self.lap_times) / len(self.lap_times) if self.lap_times else 0
        
        cursor.execute("""
            UPDATE sessions SET
                total_laps = ?,
                total_incidents = ?,
                best_lap_time = ?,
                avg_lap_time = ?
            WHERE id = ?
        """, (len(self.lap_times), self.session_incidents, best_lap, avg_lap, self.session_id))
        self.conn.commit()
        
        print("\n" + "=" * 50)
        print("📊 RESUMEN DE SESIÓN")
        print("=" * 50)
        print(f"   Vueltas totales: {len(self.lap_times)}")
        print(f"   Mejor vuelta: {self.format_time(best_lap)}")
        print(f"   Promedio: {self.format_time(avg_lap)}")
        print(f"   Incidentes: {self.session_incidents}x")
        
        if len(self.lap_times) > 1:
            consistency = max(self.lap_times) - min(self.lap_times)
            print(f"   Consistencia: ±{self.format_time(consistency)}")
        
        # Obtener stats actualizados de la API
        if self.api.connected:
            self.update_post_race_stats()
            self.fetch_official_results()
        
        print("=" * 50)
    
    @staticmethod
    def format_time(seconds):
        """Formatea segundos a mm:ss.fff"""
        if seconds <= 0:
            return "--:--.---"
        mins = int(seconds // 60)
        secs = seconds % 60
        return f"{mins}:{secs:06.3f}"
    
    def run(self):
        """Bucle principal de captura."""
        print("\n🏎️  iRacing Telemetry Logger v2")
        print("=" * 50)
        
        # Conectar a la API
        self.api.connect()
        
        # Snapshot inicial del piloto
        if self.api.connected:
            self.save_driver_snapshot()
        
        print("\nEsperando conexión con iRacing...")
        print("(Abre iRacing y entra a una sesión)")
        print("Presiona Ctrl+C para salir\n")
        
        session_started = False
        last_lap = -1
        
        try:
            while True:
                if not self.is_connected:
                    if self.connect():
                        session_started = False
                    else:
                        time.sleep(2)
                        continue
                
                if not self.ir.is_connected:
                    if session_started:
                        self.finish_session()
                    self.is_connected = False
                    session_started = False
                    print("\n⚠️  iRacing desconectado. Esperando reconexión...")
                    time.sleep(2)
                    continue
                
                self.ir.freeze_var_buffer_latest()
                
                if not session_started and self.ir['IsOnTrack']:
                    self.start_session()
                    session_started = True
                    self.session_incidents = self.ir['PlayerCarMyIncidentCount']
                
                if session_started and self.ir['IsOnTrack']:
                    current_lap = self.ir['Lap']
                    
                    if current_lap > last_lap and last_lap >= 0:
                        lap_time = self.ir['LapLastLapTime']
                        if lap_time > 0:
                            self.log_lap(last_lap, lap_time)
                    
                    last_lap = current_lap
                    self.log_telemetry(current_lap)
                
                time.sleep(POLL_RATE)
                
        except KeyboardInterrupt:
            print("\n\n👋 Cerrando logger...")
            if session_started:
                self.finish_session()
            self.disconnect()
            self.conn.close()


if __name__ == "__main__":
    logger = iRacingLogger()
    logger.run()
