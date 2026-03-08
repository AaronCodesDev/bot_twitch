from twitchio.ext import commands
import random
from phrases.games.iracing import iracing_phrases

class IracingEsMejor(commands.Cog):

    def __init__(self, bot, memoria):
        self.bot = bot
        self.memoria = memoria

    @commands.command(name="iracingesmejor")
    async def iracingesmejor(self, ctx: commands.Context):
        user = ctx.author.name.lower()
        
        # Elegir frase aleatoria
        frase = random.choice(iracing_phrases)
        respuesta = f"@{user}, {frase}"
        
        # Enviar mensaje
        await ctx.send(respuesta)
        
        # Guardar como comando en la memoria
        self.memoria.add_comando(user, "!iracingesmejor")
        
        # También puedes guardar la respuesta como "historial" si quieres
        self.memoria.add_mensaje(user, respuesta)
        
        # Guardar datos inmediatamente
        self.memoria.guardar_datos()
