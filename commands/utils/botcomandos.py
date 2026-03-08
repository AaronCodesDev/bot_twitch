from twitchio.ext import commands

class BotComandos(commands.Cog):

    def __init__(self, bot, memoria):
        self.bot = bot
        self.memoria = memoria

    @commands.command(name="botcomandos")
    async def comandos(self, ctx: commands.Context):

        mensaje1 = (
            "🤖 MIS COMANDOS | "
            "🎮 Info: !bot, !cockpit, !confianza, !misub, !nivel, !nivelconfianza, !titulo | "
            "🏁 iRacing: !piloto, !sof, !pos, !icomparar"
        )

        mensaje2 = (
            "💾 Memoria: !hechos, !olvidame, !quiensoy, !recuerda, !soy | "
            "💬 Conversación: !charla, !opina, !oye, !pregunta | "
            "😄 Diversión: !ban, !comparar, !excusa, !frasejuego, !iracingesmejor, !lemas, !topamigables"
        )

        mensaje3 = (
            "🌐 Extras: !discord, !edad, !instagram, !instantgaming, !redes, !tiktok | "
            "⭐ Subs: !misub, !topregaladas | "
            "🎉 Sorteo: !idea, !ideas, !gasolina, !sorteo | "
            "🗡️ Mods: usa !modcomandos"
        )

        await ctx.send(mensaje1)
        await ctx.send(mensaje2)
        await ctx.send(mensaje3)
