# commands/stats/topamigables.py
from twitchio.ext import commands
from core.database import db

class TopAmigables(commands.Cog):

    def __init__(self, bot, memoria):
        self.bot = bot
        self.memoria = memoria

    @commands.command(name="topamigables")
    async def top_amigables(self, ctx: commands.Context, top: str = None):
        # Limpiar caracteres invisibles y parsear
        if top:
            for char in ["\u200b", "\u200c", "\u200d", "\u2060", "͏"]:
                top = top.replace(char, "")
            top = int(top) if top.isdigit() else 5
        else:
            top = 5

        rows = db._cursor().execute("""
            SELECT username, confianza FROM user_profiles
            WHERE confianza >= 20 AND username != 'bot_fantan'
            ORDER BY confianza DESC
            LIMIT ?
        """, (top,)).fetchall()

        if not rows:
            await ctx.send("⚠️ No hay usuarios amigables aún.")
            return

        mensaje = "🏆 Usuarios más amigables: " + " | ".join(
            f"{i+1}. {r['username']} ({r['confianza']})"
            for i, r in enumerate(rows)
        )
        await ctx.send(mensaje)