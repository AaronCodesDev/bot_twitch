# commands/twitch/subsregaladas.py
from twitchio.ext import commands
from core.database import db
from datetime import datetime

class SubsRegaladas(commands.Cog):

    def __init__(self, bot, memoria):
        self.bot = bot
        self.memoria = memoria

    @commands.command(name="subsregaladas")
    async def subs_regaladas(self, ctx):
        if not (ctx.author.is_mod or ctx.author.is_broadcaster):
            await ctx.send("❌ No tienes permiso para ver las subs regaladas.")
            return

        now = datetime.now()
        rows = db._cursor().execute("""
            SELECT username, gifter FROM subs_mensuales
            WHERE tipo='regalada' AND year=? AND month=?
        """, (now.year, now.month)).fetchall()

        if not rows:
            await ctx.send("📭 Sin subs regaladas este mes.")
            return

        # Contar cuántas subs ha regalado cada gifter
        contador = {}
        detalle = []
        for r in rows:
            gifter = r["gifter"]
            receiver = r["username"]
            contador[gifter] = contador.get(gifter, 0) + 1
            detalle.append(f"@{gifter} regaló a @{receiver}")

        resumen = " | ".join(
            f"@{u}: {c} sub{'s' if c > 1 else ''}"
            for u, c in contador.items()
        )
        detalle_str = " | ".join(detalle)

        await ctx.send(f"📊 Subs regaladas este mes: {resumen} — Detalle: {detalle_str}")