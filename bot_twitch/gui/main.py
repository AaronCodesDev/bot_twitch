# gui/main.py
import flet as ft
import os
import sys
import asyncio
import threading
import traceback

# --- Configurar rutas ---
CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
BASE_DIR = os.path.abspath(os.path.join(CURRENT_DIR, ".."))
if BASE_DIR not in sys.path:
    sys.path.insert(0, BASE_DIR)

ASSETS_DIR = os.path.join(CURRENT_DIR, "assets")

from gui.app import TwitchBotApp
from core.subs_manager import SubsManager

# ----------------- ARRANCAR BOT (CREANDO LOOP PRIMERO) -----------------
def start_twitch_bot():
    """Inicia el bot creando primero el event loop"""
    
    def run_bot():
        try:
            print("🚀 Iniciando bot de Twitch...")
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            from app import BotFantan
            bot = BotFantan()
            print("✅ BotFantan instanciado correctamente")
            if hasattr(bot, 'run'):
                print("📌 Ejecutando bot.run()...")
                bot.run()
                print("✅ Bot finalizado correctamente")
            else:
                print("❌ BotFantan no tiene método 'run'")
        except Exception as e:
            print(f"❌ Error en bot: {e}")
            traceback.print_exc()
        finally:
            try:
                loop.close()
            except:
                pass
    
    thread = threading.Thread(target=run_bot, daemon=True)
    thread.start()
    return thread

# ----------------- SINCRONIZAR SUBS -----------------
def start_subs_sync():
    """Inicia la sincronización en un thread separado"""
    
    def run_sync():
        try:
            print("🔄 Sincronizando suscripciones...")
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            
            async def sync():
                subs_manager = SubsManager(debug=True)
                await subs_manager.actualizar_desde_twitch()
                print("✅ Sincronización completada")
            
            loop.run_until_complete(sync())
            loop.close()
        except Exception as e:
            print(f"❌ Error en sincronización: {e}")
            traceback.print_exc()
    
    thread = threading.Thread(target=run_sync, daemon=True)
    thread.start()
    return thread

# ----------------- MAIN -----------------
def main(page: ft.Page):
    """Función principal de la GUI"""
    page.title = "FANTAN BOT - Login"
    page.theme_mode = ft.ThemeMode.LIGHT
    
    page.window.width = 450
    page.window.height = 800
    page.window.resizable = True
    page.window.min_width = 400
    page.window.min_height = 600
    page.window.center()
    
    app = TwitchBotApp(page)
    app.run()
    
    # Solo sincronización de subs al arrancar, NO el bot
    start_subs_sync()
    
    print("✅ GUI inicializada correctamente")

# ----------------- ENTRY POINT -----------------
if __name__ == "__main__":
    ft.app(target=main, assets_dir=ASSETS_DIR)