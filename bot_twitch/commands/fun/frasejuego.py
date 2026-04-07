# commands/fun/frasejuego.py
import random
import json
import os
import aiohttp
from twitchio.ext import commands

from phrases.games.iracing import iracing_phrases
from phrases.games.valorant import valorant_phrases
from phrases.games.cs2 import cs2_phrases
from phrases.games.delta_force import delta_force_phrases
from phrases.games.ets2 import ets2_phrases
from phrases.games.dayz import dayz_phrases
from phrases.games.gta_v_rp import gta_v_rp_phrases
from phrases.games.star_citizen import star_citizen_phrases

BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
CONFIG_PATH = os.path.join(BASE_DIR, "config.json")

with open(CONFIG_PATH, "r", encoding="utf-8") as f:
    config = json.load(f)

FRASES_POR_JUEGO = {
    "iracing": iracing_phrases,
    "valorant": valorant_phrases,
    "counter-strike": cs2_phrases,
    "cs2": cs2_phrases,
    "delta force": delta_force_phrases,
    "euro truck": ets2_phrases,
    "truck simulator": ets2_phrases,
    "dayz": dayz_phrases,
    "grand theft auto": gta_v_rp_phrases,
    "gta": gta_v_rp_phrases,
    "star citizen": star_citizen_phrases,
}

class FraseJuego(commands.Cog):
    def __init__(self, bot, memoria):
        self.bot = bot
        self.memoria = memoria
        self.client_id = config["twitch"]["client_id"]
        self.token = config["twitch"]["token"].replace("oauth:", "")
        self.broadcaster_id = config["twitch"]["broadcaster_id"]

    async def get_current_game(self):
        headers = {
            "Client-ID": self.client_id,
            "Authorization": f"Bearer {self.token}"
        }
        url = f"https://api.twitch.tv/helix/channels?broadcaster_id={self.broadcaster_id}"
        async with aiohttp.ClientSession() as session:
            async with session.get(url, headers=headers) as resp:
                if resp.status == 200:
                    data = await resp.json()
                    if data["data"]:
                        return data["data"][0].get("game_name", "")
        return None

    @commands.command(name="frasejuego")
    async def test_frase_juego(self, ctx: commands.Context):
        juego_actual = await self.get_current_game()

        if not juego_actual or juego_actual.lower() in ("sin juego", "no detectado"):
            await ctx.send("⚠️ Ahora mismo no detecto ninguna categoría en el canal.")
            return

        juego_lower = juego_actual.lower()
        for clave, frases in FRASES_POR_JUEGO.items():
            if clave in juego_lower:
                await ctx.send(f"🎮 {random.choice(frases)}")
                return

        await ctx.send(f"⚠️ No tengo frases preparadas para {juego_actual}")