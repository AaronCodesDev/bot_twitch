# commands/stats/confianza.py
from twitchio.ext import commands
from core.database import db

class Confianza(commands.Cog):

    def __init__(self, bot, memoria):
        self.bot = bot
        self.memoria = memoria

    def _nivel_confianza(self, confianza: int) -> str:
        if confianza >= 1000:
            return "🟢 Amigable"
        elif confianza >= 501:
            return "🟡 Neutral"
        return "🔴 Antipático"

    @commands.command(name="confianza")
    async def confianza(self, ctx: commands.Context, target_user: str = None):
        autor = ctx.author.name.lower()
        usuario = autor if not target_user or not target_user.strip() else target_user.lstrip("@").lower()

        if usuario == "bot_fantan":
            await ctx.send(f"@{ctx.author.name}, de ese bot no hablo... 🤬🤐")
            return

        confianza = db.get_confianza(usuario)
        nivel = self._nivel_confianza(confianza)

        if usuario == autor:
            await ctx.send(f"@{ctx.author.name}, tu confianza es {confianza} → {nivel} 😏")
        else:
            await ctx.send(f"@{ctx.author.name}, @{usuario} tiene {confianza} de confianza → {nivel} 😏")