from twitchio.ext import commands

class NivelConfianza(commands.Cog):
    def __init__(self, bot, memoria):
        self.bot = bot
        self.memoria = memoria

    @commands.command(name="nivelconfianza")
    async def mostrar_niveles_confianza(self, ctx: commands.Context):
        """Muestra los niveles de confianza y su significado."""
        mensaje = (
            "📊 Niveles de confianza:\n"
            "🔴 0 - 500: Antipático\n"
            "🟡 501 - 999: Neutral\n"
            "🟢 1000+: Amigable\n\n"
            "Usa !confianza <usuario> para ver su nivel actual."
        )
        await ctx.send(mensaje)
