# commands/twitch/titulo_directo.py
from twitchio.ext import commands
import aiohttp
import json
import os

BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
CONFIG_PATH = os.path.join(BASE_DIR, "config.json")

with open(CONFIG_PATH, "r", encoding="utf-8") as f:
    config = json.load(f)

class TituloDirecto(commands.Cog):
    def __init__(self, bot, memoria):
        self.bot = bot
        self.memoria = memoria
        self.client_id = config["twitch"]["client_id"]
        self.token = config["twitch"]["token"].replace("oauth:", "")
        self.channel_name = config["twitch"]["channel"]
        self.broadcaster_id = config["twitch"]["broadcaster_id"]

    async def get_stream_info(self):
        headers = {
            "Client-ID": self.client_id,
            "Authorization": f"Bearer {self.token}"
        }
        async with aiohttp.ClientSession() as session:
            # Stream activo
            async with session.get(
                "https://api.twitch.tv/helix/streams",
                headers=headers,
                params={"user_login": self.channel_name}
            ) as resp:
                if resp.status == 200:
                    data = await resp.json()
                    if data.get("data"):
                        stream = data["data"][0]
                        titulo = stream.get("title", "Sin título")
                        game_id = stream.get("game_id")
                        juego = "No detectado"
                        if game_id:
                            async with session.get(
                                "https://api.twitch.tv/helix/games",
                                headers=headers,
                                params={"id": game_id}
                            ) as gresp:
                                if gresp.status == 200:
                                    gdata = await gresp.json()
                                    if gdata.get("data"):
                                        juego = gdata["data"][0].get("name", "No detectado")
                        return titulo, juego, True

            # Canal offline
            async with session.get(
                f"https://api.twitch.tv/helix/channels?broadcaster_id={self.broadcaster_id}",
                headers=headers
            ) as resp:
                if resp.status == 200:
                    data = await resp.json()
                    if data.get("data"):
                        info = data["data"][0]
                        return info.get("title", "Sin título"), info.get("game_name", "No detectado"), False

        return "Sin título", "No detectado", False

    @commands.command(name="titulo", aliases=["streaminfo"])
    async def titulo_directo(self, ctx: commands.Context):
        titulo, juego, online = await self.get_stream_info()
        if online:
            await ctx.send(f"🎬 Título actual: '{titulo}' | 🎮 Juego: {juego}")
        else:
            await ctx.send(f"⚠️ Canal OFFLINE. Último título conocido: '{titulo}' | Juego: {juego}")