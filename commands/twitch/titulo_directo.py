from twitchio.ext import commands
import aiohttp
import json

with open("config.json", "r", encoding="utf-8") as f:
    config = json.load(f)

class TituloDirecto(commands.Cog):
    def __init__(self, bot, memoria):
        self.bot = bot
        self.memoria = memoria
        self.client_id = config["twitch"]["client_id"]
        self.token = config["twitch"]["token"].replace("oauth:", "")
        self.channel_name = config["twitch"]["channel"]
        self.broadcaster_id = config["twitch"]["broadcaster_id"]  # Debe ser numérico

    async def get_stream_info(self):
        """
        Obtiene título y juego del canal Fantan.
        Devuelve el stream activo si hay, o el último título configurado si está offline.
        """
        headers = {
            "Client-ID": self.client_id,
            "Authorization": f"Bearer {self.token}"
        }

        async with aiohttp.ClientSession() as session:
            # --- Intentar obtener stream activo ---
            stream_url = "https://api.twitch.tv/helix/streams"
            params = {"user_login": self.channel_name}
            async with session.get(stream_url, headers=headers, params=params) as resp:
                if resp.status == 200:
                    data = await resp.json()
                    streams = data.get("data", [])
                    if streams:
                        # Canal online
                        stream = streams[0]
                        titulo = stream.get("title", "Sin título")
                        game_id = stream.get("game_id")
                        juego = "No detectado"

                        if game_id:
                            games_url = "https://api.twitch.tv/helix/games"
                            async with session.get(games_url, headers=headers, params={"id": game_id}) as gresp:
                                if gresp.status == 200:
                                    gdata = await gresp.json()
                                    if gdata.get("data"):
                                        juego = gdata["data"][0].get("name", "No detectado")
                        return titulo, juego, True  # Canal online

            # --- Si no hay stream activo, obtener título configurado offline ---
            channel_url = f"https://api.twitch.tv/helix/channels?broadcaster_id={self.broadcaster_id}"
            async with session.get(channel_url, headers=headers) as resp:
                if resp.status == 200:
                    data = await resp.json()
                    if "data" in data and len(data["data"]) > 0:
                        info = data["data"][0]
                        titulo = info.get("title", "Sin título")
                        juego = info.get("game_name", "No detectado")
                        return titulo, juego, False  # Canal offline

        # --- Fallback si falla la API ---
        return "Sin título", "No detectado", False

    @commands.command(name="titulo", aliases=["streaminfo"])
    async def titulo_directo(self, ctx: commands.Context):
        """
        Comando que envía al chat el título y juego del canal.
        """
        titulo, juego, online = await self.get_stream_info()
        if online:
            await ctx.send(f"🎬 Título actual: '{titulo}' | 🎮 Juego: {juego}")
        else:
            await ctx.send(f"⚠️ Canal OFFLINE. Último título conocido: '{titulo}' | Juego: {juego}")
