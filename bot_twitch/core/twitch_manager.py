# core/twitch_manager.py
import json
import os
import aiohttp
from datetime import datetime, timezone
from core.subs_manager import SubsManager

# Cargar config — ruta absoluta para que funcione desde cualquier CWD
_CONFIG_PATH = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "config.json")
with open(_CONFIG_PATH, "r", encoding="utf-8") as f:
    CONFIG = json.load(f)

TWITCH = CONFIG["twitch"]

class TwitchManager:
    def __init__(self):
        self.client_id = TWITCH["client_id"]
        self.oauth_token = TWITCH["token"].replace("oauth:", "")
        self.broadcaster_id = TWITCH["broadcaster_id"]
        # SubsManager para guardar directamente en DB
        self.subs_manager = SubsManager()

    async def actualizar_subs_desde_api(self):
        """Obtiene subs desde la API y los guarda en SQLite directamente."""
        url = "https://api.twitch.tv/helix/subscriptions"
        headers = {
            "Client-ID": self.client_id,
            "Authorization": f"Bearer {self.oauth_token}"
        }

        try:
            async with aiohttp.ClientSession() as session:
                suscriptores_api = []
                cursor = None
                print("⏳ Obteniendo suscriptores actuales de la API de Twitch...")

                while True:
                    params = {"broadcaster_id": self.broadcaster_id, "first": 100}
                    if cursor:
                        params["after"] = cursor

                    async with session.get(url, headers=headers, params=params) as resp:
                        if resp.status != 200:
                            error_text = await resp.text()
                            print(f"❌ Error API Twitch ({resp.status}): {error_text}")
                            return False

                        data = await resp.json()
                        suscriptores_api.extend(data.get("data", []))
                        cursor = data.get("pagination", {}).get("cursor")
                        if not cursor:
                            break

            # Guardamos directamente en SQLite
            ahora = datetime.now(timezone.utc).isoformat()
            escritos_count = 0
            for s in suscriptores_api:
                username = s["user_name"].lower()
                tier_val = s.get("tier", "1000")
                tier_label = int(tier_val) // 1000  # 1, 2, 3

                # Meses/tenure según API
                meses = int(s.get("tenure", 1)) if "tenure" in s else 1

                self.subs_manager.guardar_sub(
                    tipo="normal",
                    tier=tier_label,
                    usuario=username,
                    meses=meses,
                    fecha=ahora
                )
                escritos_count += 1

            print(f"✅ Subs guardados en DB: {escritos_count}")
            return True

        except Exception as e:
            print(f"❌ Error crítico en TwitchManager: {e}")
            return False