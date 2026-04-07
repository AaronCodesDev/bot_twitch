import asyncio
import random
import irsdk

from phrases.iracing.x1 import X1_PHRASES
from phrases.iracing.x2 import X2_PHRASES
from phrases.iracing.x4 import X4_PHRASES


def safe_var(ir, var_name):
    try:
        val = ir[var_name]
        return val if val is not None else 0
    except Exception:
        return 0


class IRacingListener:
    def __init__(self, bot):
        self.bot = bot
        self.ir = irsdk.IRSDK()
        self.last_incidents = 0
        self.running = False
        self.last_irating = None
        self.last_sr = None

    # ───────── Métodos seguros para obtener datos ─────────
    def get_player_irating(self):
        try:
            if not self.ir.is_initialized:
                return None
            idx = self.ir["DriverInfo"]["DriverCarIdx"]
            return self.ir["DriverInfo"]["Drivers"][idx]["IRating"]
        except Exception:
            return None

    def get_player_sr(self):
        try:
            if not self.ir.is_initialized:
                return None
            idx = self.ir["DriverInfo"]["DriverCarIdx"]
            return self.ir["DriverInfo"]["Drivers"][idx]["LicString"]
        except Exception:
            return None

    def get_player_split(self):
        try:
            idx = self.ir["DriverInfo"]["DriverCarIdx"]
            return self.ir["DriverInfo"]["Drivers"][idx].get("Split", "Desconocido")
        except Exception:
            return "Desconocido"

    def get_player_sof(self):
        try:
            session_num = self.ir["SessionNum"]
            sessions = self.ir["SessionInfo"]["Sessions"]
            if session_num is not None and session_num < len(sessions):
                return sessions[session_num].get("StrengthOfField", "Desconocido")
            return "Desconocido"
        except Exception:
            return "Desconocido"

    # ───────── Loop principal ─────────
    async def start(self):
        wait = 30
        max_waits = 300

        while not self.ir.startup():
            print(f"❌ iRacing no está activo, reintentando en {wait}s...")
            await asyncio.sleep(wait)
            wait = min(wait * 2, max_waits)

        print("🎮 iRacing Conectado")
        self.running = True
        await asyncio.sleep(1)
        self.ir.freeze_var_buffer_latest()
        self.last_incidents = safe_var(self.ir, "PlayerCarMyIncidentCount")

        while self.running:
            try:
                self.ir.freeze_var_buffer_latest()

                if not self.ir.is_initialized:
                    await asyncio.sleep(1)
                    continue

                # ───────── Detectar incidentes ─────────
                current_incidents = safe_var(self.ir, "PlayerCarMyIncidentCount")
                diff = current_incidents - self.last_incidents

                if diff > 0:
                    frase = None
                    if diff == 1:
                        frase = random.choice(X1_PHRASES)
                    elif diff == 2:
                        frase = random.choice(X2_PHRASES)
                    elif diff >= 4:
                        frase = random.choice(X4_PHRASES)

                    if frase:
                        await self.send_to_chat(frase)

                self.last_incidents = current_incidents

                # ───────── Detectar cambios de iRating ─────────
                current_ir = self.get_player_irating()
                current_sr = self.get_player_sr()

                if current_ir is not None and self.last_irating is not None:
                    if current_ir != self.last_irating:
                        diff_ir = current_ir - self.last_irating
                        if diff_ir > 0:
                            msg = f"📈 Fantan gana {diff_ir} iR → {current_ir} iR PogChamp"
                        else:
                            msg = f"📉 Fantan pierde {abs(diff_ir)} iR → {current_ir} iR KEKW"
                        await self.send_to_chat(msg)
                self.last_irating = current_ir
                self.last_sr = current_sr

                await asyncio.sleep(0.3)

            except Exception as e:
                print(f"⚠️ Error iRacing listener: {e}")
                await asyncio.sleep(1)

    # ───────── Enviar mensaje al chat ─────────
    async def send_to_chat(self, texto):
        for ch in self.bot.connected_channels:
            await ch.send(texto)

    def stop(self):
        self.running = False
