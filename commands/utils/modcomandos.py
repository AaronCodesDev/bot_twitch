from twitchio.ext import commands

class ModComandos(commands.Cog):

    def __init__(self, bot, memoria):
        self.bot = bot
        self.memoria = memoria

    @commands.command(name="modcomandos")
    async def mod_comandos(self, ctx: commands.Context):

        if ctx.author.is_mod or ctx.author.is_broadcaster:
            await ctx.send(
                "🗡️ MOD: !addcomando, !delcomando, !favorito, !guardar, "
                "!olvidarideas, !olvidartodo, !promo, !quesabesde, !salir, "
                "!so, !subs, !subsregaladas, !unfavorito"
            )
