import random
from twitchio.ext import commands
import json

# --- CARGAR CONFIG ---
with open("config.json", "r", encoding="utf-8") as f:
    config = json.load(f)

# --- COG CLIP ---
class Clip(commands.Cog):
    def __init__(self, bot, memory=None):
        self.bot = bot
        self.memory = memory
        self.channel = config['twitch']['channel']

    @commands.command(name="clip")
    async def clip(self, ctx: commands.Context):
        """Envía un clip gracioso del usuario."""
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
        frase = random.choice(frases_clip)
        enlace_clip = f"https://www.twitch.tv/{self.channel}/clip"
        await ctx.send(f"{frase} {enlace_clip}")
