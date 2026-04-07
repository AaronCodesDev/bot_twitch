#!/usr/bin/env python3
"""
iRacing Data Analyzer v2
Analiza tus datos de carrera incluyendo iRating y Safety Rating.
"""

import sqlite3
import json
from pathlib import Path
from datetime import datetime, timedelta

DB_PATH = Path(__file__).parent / "iracing_data.db"


def format_time(seconds):
    """Formatea segundos a mm:ss.fff"""
    if not seconds or seconds <= 0:
        return "--:--.---"
    mins = int(seconds // 60)
    secs = seconds % 60
    return f"{mins}:{secs:06.3f}"


class iRacingAnalyzer:
    def __init__(self):
        self.conn = sqlite3.connect(DB_PATH)
        self.conn.row_factory = sqlite3.Row
    
    def get_current_stats(self):
        """Obtiene las estadísticas más recientes del piloto."""
        cursor = self.conn.cursor()
        cursor.execute("""
            SELECT * FROM driver_profile
            ORDER BY timestamp DESC
            LIMIT 1
        """)
        return cursor.fetchone()
    
    def get_irating_history(self, limit=50):
        """Historial de iRating."""
        cursor = self.conn.cursor()
        cursor.execute("""
            SELECT 
                session_date,
                track_name,
                car_name,
                irating_before,
                irating_after,
                irating_change,
                sr_before,
                sr_after,
                sr_change,
                finish_position,
                total_incidents
            FROM sessions
            WHERE irating_change IS NOT NULL
            ORDER BY session_date DESC
            LIMIT ?
        """, (limit,))
        return cursor.fetchall()
    
    def get_all_sessions(self, limit=20):
        """Lista las últimas sesiones."""
        cursor = self.conn.cursor()
        cursor.execute("""
            SELECT * FROM sessions
            ORDER BY session_date DESC
            LIMIT ?
        """, (limit,))
        return cursor.fetchall()
    
    def get_session_laps(self, session_id):
        """Obtiene todas las vueltas de una sesión."""
        cursor = self.conn.cursor()
        cursor.execute("""
            SELECT * FROM laps
            WHERE session_id = ?
            ORDER BY lap_number
        """, (session_id,))
        return cursor.fetchall()
    
    def get_track_stats(self, track_name, car_name=None):
        """Estadísticas en una pista específica."""
        cursor = self.conn.cursor()
        
        query = """
            SELECT 
                COUNT(DISTINCT s.id) as total_sessions,
                SUM(s.total_laps) as total_laps,
                MIN(l.lap_time) as best_lap,
                AVG(l.lap_time) as avg_lap,
                SUM(s.total_incidents) as total_incidents,
                SUM(CASE WHEN s.irating_change > 0 THEN 1 ELSE 0 END) as positive_races,
                SUM(CASE WHEN s.irating_change < 0 THEN 1 ELSE 0 END) as negative_races,
                AVG(s.irating_change) as avg_irating_change
            FROM sessions s
            LEFT JOIN laps l ON s.id = l.session_id
            WHERE s.track_name LIKE ?
            AND (l.lap_time > 0 OR l.lap_time IS NULL)
        """
        params = [f"%{track_name}%"]
        
        if car_name:
            query += " AND s.car_name LIKE ?"
            params.append(f"%{car_name}%")
        
        cursor.execute(query, params)
        return cursor.fetchone()
    
    def get_consistency_score(self, session_id):
        """Calcula el score de consistencia de una sesión."""
        laps = self.get_session_laps(session_id)
        valid_laps = [l['lap_time'] for l in laps if l['lap_time'] and l['lap_time'] > 0 and not l['pit_stop']]
        
        if len(valid_laps) < 3:
            return None
        
        avg_time = sum(valid_laps) / len(valid_laps)
        variance = sum((t - avg_time) ** 2 for t in valid_laps) / len(valid_laps)
        std_dev = variance ** 0.5
        
        return {
            'std_dev': std_dev,
            'range': max(valid_laps) - min(valid_laps),
            'best': min(valid_laps),
            'worst': max(valid_laps),
            'avg': avg_time,
            'total_laps': len(valid_laps)
        }
    
    def get_incident_analysis(self, last_n_sessions=20):
        """Analiza patrones de incidentes."""
        cursor = self.conn.cursor()
        cursor.execute("""
            SELECT 
                l.lap_number,
                SUM(l.incidents_this_lap) as total_incidents,
                COUNT(*) as lap_count
            FROM laps l
            JOIN sessions s ON l.session_id = s.id
            WHERE l.session_id IN (
                SELECT id FROM sessions ORDER BY session_date DESC LIMIT ?
            )
            GROUP BY l.lap_number
            HAVING total_incidents > 0
            ORDER BY l.lap_number
        """, (last_n_sessions,))
        return cursor.fetchall()
    
    def get_car_performance(self):
        """Rendimiento por coche."""
        cursor = self.conn.cursor()
        cursor.execute("""
            SELECT 
                car_name,
                COUNT(*) as races,
                SUM(CASE WHEN irating_change > 0 THEN 1 ELSE 0 END) as wins_ir,
                SUM(CASE WHEN irating_change < 0 THEN 1 ELSE 0 END) as losses_ir,
                AVG(irating_change) as avg_ir_change,
                AVG(sr_change) as avg_sr_change,
                SUM(total_incidents) as total_incidents,
                SUM(total_laps) as total_laps
            FROM sessions
            WHERE session_type = 'Race'
            GROUP BY car_name
            ORDER BY races DESC
        """)
        return cursor.fetchall()
    
    def print_career_summary(self):
        """Imprime resumen de carrera con iRating/SR."""
        stats = self.get_current_stats()
        history = self.get_irating_history(30)
        
        print("\n" + "=" * 60)
        print("🏆 TU CARRERA EN iRACING")
        print("=" * 60)
        
        if stats:
            print(f"\n👤 Piloto: {stats['display_name']}")
            print(f"   Customer ID: {stats['cust_id']}")
            print(f"\n📊 Estadísticas Road:")
            print(f"   iRating: {stats['irating_road']}")
            print(f"   Safety Rating: {stats['sr_road']}")
            print(f"   Licencia: {stats['license_road']}")
            print(f"   Vueltas: {stats['laps_road']}")
            print(f"   Victorias: {stats['wins_road']}")
            print(f"   Carreras: {stats['starts_road']}")
        
        if history:
            # Calcular tendencias
            recent_changes = [h['irating_change'] for h in history if h['irating_change']]
            if recent_changes:
                total_change = sum(recent_changes)
                positive = len([c for c in recent_changes if c > 0])
                negative = len([c for c in recent_changes if c < 0])
                
                print(f"\n📈 Últimas {len(recent_changes)} carreras:")
                print(f"   Cambio total iRating: {total_change:+d}")
                print(f"   Carreras positivas: {positive}")
                print(f"   Carreras negativas: {negative}")
                print(f"   Win rate: {positive/(positive+negative)*100:.1f}%")
        
        print("\n" + "=" * 60)
    
    def print_irating_history(self):
        """Muestra historial de iRating."""
        history = self.get_irating_history(20)
        
        print("\n" + "=" * 60)
        print("📈 HISTORIAL DE iRATING")
        print("=" * 60)
        
        if not history:
            print("   No hay datos de carreras oficiales todavía.")
            return
        
        print(f"\n{'Fecha':<12} {'Pista':<20} {'iR Antes':<8} {'Cambio':<8} {'Inc':<4}")
        print("-" * 60)
        
        for race in history:
            date = race['session_date'][:10] if race['session_date'] else 'N/A'
            track = (race['track_name'] or 'Unknown')[:18]
            ir_before = race['irating_before'] or 0
            ir_change = race['irating_change'] or 0
            incidents = race['total_incidents'] or 0
            
            symbol = "🟢" if ir_change >= 0 else "🔴"
            print(f"{date:<12} {track:<20} {ir_before:<8} {symbol} {ir_change:+5d}  {incidents}x")
        
        print("=" * 60)
    
    def print_car_stats(self):
        """Estadísticas por coche."""
        cars = self.get_car_performance()
        
        print("\n" + "=" * 60)
        print("🚗 RENDIMIENTO POR COCHE")
        print("=" * 60)
        
        if not cars:
            print("   No hay datos de carreras todavía.")
            return
        
        for car in cars:
            win_rate = 0
            if car['wins_ir'] or car['losses_ir']:
                win_rate = car['wins_ir'] / (car['wins_ir'] + car['losses_ir']) * 100
            
            inc_per_lap = 0
            if car['total_laps'] and car['total_laps'] > 0:
                inc_per_lap = (car['total_incidents'] or 0) / car['total_laps']
            
            print(f"\n   {car['car_name']}")
            print(f"   Carreras: {car['races']}")
            print(f"   Win Rate (iR): {win_rate:.1f}%")
            print(f"   Avg iR change: {car['avg_ir_change'] or 0:+.1f}")
            print(f"   Inc/vuelta: {inc_per_lap:.3f}")
        
        print("\n" + "=" * 60)
    
    def print_session_detail(self, session_id):
        """Imprime detalles de una sesión específica."""
        cursor = self.conn.cursor()
        cursor.execute("SELECT * FROM sessions WHERE id = ?", (session_id,))
        session = cursor.fetchone()
        
        if not session:
            print(f"Sesión {session_id} no encontrada")
            return
        
        laps = self.get_session_laps(session_id)
        consistency = self.get_consistency_score(session_id)
        
        print("\n" + "=" * 60)
        print(f"📋 SESIÓN #{session_id}")
        print("=" * 60)
        print(f"   Fecha: {session['session_date']}")
        print(f"   Pista: {session['track_name']} ({session['track_config']})")
        print(f"   Coche: {session['car_name']}")
        print(f"   Tipo: {session['session_type']}")
        
        if session['sof']:
            print(f"   SOF: {session['sof']}")
        
        print(f"   Vueltas: {session['total_laps']}")
        print(f"   Incidentes: {session['total_incidents']}x")
        
        if session['best_lap_time']:
            print(f"\n⏱️  Tiempos:")
            print(f"   Mejor: {format_time(session['best_lap_time'])}")
            print(f"   Promedio: {format_time(session['avg_lap_time'])}")
        
        if session['irating_change'] is not None:
            symbol = "📈" if session['irating_change'] >= 0 else "📉"
            print(f"\n{symbol} Resultado:")
            print(f"   iRating: {session['irating_before']} → {session['irating_after']} ({session['irating_change']:+d})")
            print(f"   SR: {session['sr_before']:.2f} → {session['sr_after']:.2f} ({session['sr_change']:+.2f})")
        
        if consistency:
            print(f"\n📊 Consistencia:")
            print(f"   Desv. estándar: {consistency['std_dev']:.3f}s")
            print(f"   Rango: {consistency['range']:.3f}s")
        
        print(f"\n📝 Vueltas:")
        for lap in laps:
            if lap['lap_time'] and lap['lap_time'] > 0:
                inc = f" ⚠️ +{lap['incidents_this_lap']}x" if lap['incidents_this_lap'] else ""
                pit = " 🔧 PIT" if lap['pit_stop'] else ""
                print(f"   V{lap['lap_number']:3d}: {format_time(lap['lap_time'])}  P{lap['position'] or '?'}{inc}{pit}")
        
        print("=" * 60)


def main():
    analyzer = iRacingAnalyzer()
    
    while True:
        print("\n🏎️  iRacing Analyzer v2")
        print("-" * 30)
        print("1. Resumen de carrera")
        print("2. Historial de iRating")
        print("3. Estadísticas por coche")
        print("4. Ver sesiones recientes")
        print("5. Detalle de sesión")
        print("6. Estadísticas por pista")
        print("7. Análisis de incidentes")
        print("8. Salir")
        
        choice = input("\nElige una opción: ").strip()
        
        if choice == "1":
            analyzer.print_career_summary()
        
        elif choice == "2":
            analyzer.print_irating_history()
        
        elif choice == "3":
            analyzer.print_car_stats()
        
        elif choice == "4":
            sessions = analyzer.get_all_sessions()
            print("\n📋 Últimas sesiones:")
            for s in sessions:
                ir_change = f" ({s['irating_change']:+d})" if s['irating_change'] else ""
                print(f"   [{s['id']}] {s['session_date'][:16]} - {s['track_name']} / {s['car_name']}{ir_change}")
        
        elif choice == "5":
            session_id = input("ID de sesión: ").strip()
            if session_id.isdigit():
                analyzer.print_session_detail(int(session_id))
        
        elif choice == "6":
            track = input("Nombre de pista: ").strip()
            stats = analyzer.get_track_stats(track)
            if stats and stats['total_sessions']:
                print(f"\n📊 Estadísticas en {track}:")
                print(f"   Sesiones: {stats['total_sessions']}")
                print(f"   Vueltas: {stats['total_laps'] or 0}")
                print(f"   Mejor vuelta: {format_time(stats['best_lap'])}")
                print(f"   Carreras iR+: {stats['positive_races'] or 0}")
                print(f"   Carreras iR-: {stats['negative_races'] or 0}")
                print(f"   Avg iR change: {stats['avg_irating_change'] or 0:+.1f}")
            else:
                print(f"No hay datos para '{track}'")
        
        elif choice == "7":
            incidents = analyzer.get_incident_analysis()
            print("\n⚠️  Incidentes por vuelta (últimas 20 sesiones):")
            if incidents:
                for inc in incidents:
                    bar = "█" * min(inc['total_incidents'], 20)
                    print(f"   Vuelta {inc['lap_number']:2d}: {bar} ({inc['total_incidents']})")
            else:
                print("   No hay datos de incidentes")
        
        elif choice == "8":
            print("👋 ¡Hasta la próxima!")
            break


if __name__ == "__main__":
    main()
