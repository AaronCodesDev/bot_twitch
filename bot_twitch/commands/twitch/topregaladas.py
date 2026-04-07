# commands/twitch/topregaladas.py
from twitchio.ext import commands
from core.database import db
from datetime import datetime

class TopRegaladas(commands.Cog):

    def __init__(self, bot, memoria):
        self.bot = bot
        self.memoria = memoria

    @commands.command(name="topregaladas")
    async def top_regaladas(self, ctx):
        now = datetime.now()
        rows = db._cursor().execute("""
            SELECT gifter, COUNT(*) as total FROM subs_mensuales
            WHERE tipo='regalada' AND year=? AND month=?
            GROUP BY gifter
            ORDER BY total DESC
        """, (now.year, now.month)).fetchall()

        if not rows:
            await ctx.send("📭 Sin subs regaladas este mes. El capitalismo está fallando.")
            return

        mensajes = []
        for i, r in enumerate(rows, 1):
            u = r["gifter"]
            c = r["total"]
            if c == 1:
                msg = f"{i}. @{u}: {c} sub… valiente, pero podrías esforzarte más 😅"
            elif c == 2:
                msg = f"{i}. @{u}: {c} subs, repartiendo cariño moderadamente 😏"
            elif 3 <= c <= 5:
                msg = f"{i}. @{u}: {c} subs, casi Santa Claus 🎅 pero aún te falta"
            elif 6 <= c <= 10:
                msg = f"{i}. @{u}: {c} subs, héroe del mes 🦸‍♂️🔥"
            else:
                msg = f"{i}. @{u}: {c} subs, leyenda viva ⚡💥 ya deberías tener estatua"
            mensajes.append(msg)

        await ctx.send(
            f"🏆 Top regaladores este mes ({len(rows)} en total): " +
            " | ".join(mensajes)
        )