from twitchio.ext import commands
import random
from phrases.common.sarcastic import sarcastic_phrases

class Excusa(commands.Cog):

    def __init__(self, bot, memoria):
        self.bot = bot
        self.memoria = memoria

    @commands.command(name="excusa")
    async def excusa(self, ctx: commands.Context):
        user = ctx.author.name.lower()

        frase = random.choice(sarcastic_phrases)
        respuesta = f"@{user}, {frase}"

        await ctx.send(respuesta)

        # 🔹 Guardar como COMANDO
        self.memoria.add_recuerdo(user, "!excusa")

        # 🔹 Llamada segura a guardar_datos
        if hasattr(self.memoria, "guardar_datos"):
            self.memoria.guardar_datos()
