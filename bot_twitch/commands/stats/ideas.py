# commands/stats/ideas.py
from twitchio.ext import commands
from core.database import db

class Ideas(commands.Cog):

    def __init__(self, bot, memoria):
        self.bot = bot
        self.memoria = memoria

    @commands.command(name="ideas")
    async def listar_ideas(self, ctx: commands.Context):
        if not (ctx.author.is_mod or ctx.author.is_broadcaster):
            await ctx.send("❌ No tienes permiso para ver las ideas.")
            return

        ideas = db.get_all_ideas()

        if not ideas:
            await ctx.send("📭 No hay ideas registradas todavía.")
            return

        ultimas = ideas[-5:]
        mensaje = "💡 Últimas ideas: " + " | ".join(
            f"{i['usuario']}: {i['idea'][:40]}" for i in ultimas
        )
        await ctx.send(mensaje)