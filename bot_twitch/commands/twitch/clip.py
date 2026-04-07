# commands/twitch/clip.py
import random
import json
import os
from twitchio.ext import commands

BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
CONFIG_PATH = os.path.join(BASE_DIR, "config.json")

with open(CONFIG_PATH, "r", encoding="utf-8") as f:
    config = json.load(f)

class Clip(commands.Cog):
    def __init__(self, bot, memory=None):
        self.bot = bot
        self.memory = memory
        self.channel = config["twitch"]["channel"]

    @commands.command(name="clip")
    async def clip(self, ctx: commands.Context):
        user = ctx.author.name.lower()
        frases_clip = [
            f"@{user}, ¡haz clip antes de que olvides otra vez dónde dejaste tu cerebro! 🎥",
            f"Atención @{user}: momento épico. Sí, incluso tú puedes intentar no romper nada esta vez. 📸",
            f"Este instante merece ser recordado, @{user}, porque nunca volverás a ser relevante. 😏",
            f"Clip o no clip, @{user}, tus errores seguirán ahí… pero al menos se verán mejor. 🎬",
            f"¡Rápido! @{user}, antes de que tu habilidad desaparezca como tu dignidad. 📸",
            f"Momento legendario capturado para la posteridad… o al menos para burlarse de @{user}. 😂",
            f"@{user}, haz clip antes de que alguien borre tu historial de vergüenza. 🎥",
            f"Sí, @{user}, incluso tú puedes ser protagonista por 5 segundos… aprovéchalo. 😎",
            f"Clip inmediato, @{user}, porque la historia te recordará… aunque no quieras. 📸",
            f"¡No esperes más, @{user}! Tu momento de gloria fugaz está a un clic de distancia. 🎬"
        ]
        await ctx.send(f"{random.choice(frases_clip)} https://www.twitch.tv/{self.channel}/clip")