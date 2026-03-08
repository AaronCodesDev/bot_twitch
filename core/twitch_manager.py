import json
import aiohttp
import csv
import os
from datetime import datetime, timezone

# Cargar config
with open("config.json", "r", encoding="utf-8") as f:
    CONFIG = json.load(f)

TWITCH = CONFIG["twitch"]

class TwitchManager:
    def __init__(self):
        self.client_id = TWITCH["client_id"]
        self.oauth_token = TWITCH["token"].replace("oauth:", "")
        self.broadcaster_id = TWITCH["broadcaster_id"]
        self.import_path = os.path.join('data', 'imports', 'subscriber-list.csv')

    async def actualizar_csv_desde_twitch(self):
        os.makedirs(os.path.dirname(self.import_path), exist_ok=True)
        
        # 1. LEER EL CSV ACTUAL PARA MANTENER LAS FECHAS ANTIGUAS (HISTORIAL)
        historial_datos = {}
        if os.path.exists(self.import_path):
            try:
                with open(self.import_path, "r", encoding="utf-8") as f:
                    reader = csv.DictReader(f)
                    for row in reader:
                        if row.get("Username"):
                            historial_datos[row["Username"].lower()] = row
            except Exception as e:
                print(f"⚠️ No se pudo cargar el historial: {e}")

        # 2. OBTENER DATOS ACTUALES DE LA API
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
                        current_batch = data.get("data", [])
                        suscriptores_api.extend(current_batch)
                        
                        cursor = data.get("pagination", {}).get("cursor")
                        if not cursor:
                            break

            # 3. ESCRIBIR EL NUEVO CSV
            # IMPORTANTE: No filtramos al broadcaster para asegurar que el archivo tenga datos si solo estás tú.
            with open(self.import_path, "w", newline="", encoding="utf-8") as f:
                fieldnames = ["Username", "Subscribe Date", "Current Tier", "Tenure", "Streak", "Sub Type", "Founder"]
                writer = csv.DictWriter(f, fieldnames=fieldnames)
                writer.writeheader()
                
                escribiendo_count = 0
                for s in suscriptores_api:
                    username = s["user_name"].lower()
                    
                    # --- LÓGICA DE PERSISTENCIA ---
                    if username in historial_datos:
                        row_data = historial_datos[username]
                        sub_date = row_data.get("Subscribe Date")
                        tenure = row_data.get("Tenure", "1")
                        streak = row_data.get("Streak", "1")
                        sub_type = row_data.get("Sub Type", "recurring")
                        founder = row_data.get("Founder", "false")
                    else:
                        raw_date = s.get("started_at", "")
                        if raw_date:
                            dt_obj = datetime.fromisoformat(raw_date.replace("Z", "+00:00"))
                            sub_date = dt_obj.strftime("%Y-%m-%dT%H:%M:%SZ")
                        else:
                            sub_date = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
                        
                        tenure = "1"
                        streak = "1"
                        sub_type = "gift" if s.get("is_gift") else "recurring"
                        founder = "false"

                    # El Tier siempre lo actualizamos según la API
                    tier_val = s.get("tier", "1000")
                    tier_label = f"Tier {int(tier_val) // 1000}"

                    writer.writerow({
                        "Username": username,
                        "Subscribe Date": sub_date,
                        "Current Tier": tier_label,
                        "Tenure": tenure,
                        "Streak": streak,
                        "Sub Type": sub_type,
                        "Founder": founder
                    })
                    escribiendo_count += 1

            print(f"✅ CSV actualizado correctamente. Subs escritos: {escribiendo_count}")
            return True

        except Exception as e:
            print(f"❌ Error crítico en TwitchManager: {e}")
            return False