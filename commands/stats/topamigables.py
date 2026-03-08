from twitchio.ext import commands
from core.memory import Memory
from typing import Optional
import os


class TopAmigables(commands.Cog):

    def __init__(self, bot, memoria: Memory):
        self.bot = bot
        self.memoria = memoria
        
    @commands.command(name="topamigables")
    async def top_amigables(self, ctx: commands.Context, top: str = None):

        if top:
            for char in ["\u200b", "\u200c", "\u200d", "\u2060", "͏"]:
                top = top.replace(char, "")

            if not top.isdigit():
                top = 5
            else:
                top = int(top)
        else:
            top = 5

        users = {}

        for filename in os.listdir(self.memoria.users_dir):
            if not filename.endswith(".json"):
                continue

            user = filename.replace(".json", "")
            data = self.memoria._load_user(user)
            users[user] = data

        amigables = {
            u: datos.get("confianza", 0)
            for u, datos in users.items()
            if datos.get("confianza", 0) >= 20
            and u.lower() != "bot_fantan"
        }

        if not amigables:
            await ctx.send("⚠️ No hay usuarios amigables aún.")
            return

        ranking = sorted(amigables.items(), key=lambda x: x[1], reverse=True)
        top_list = ranking[:top]

        mensaje = "🏆 Usuarios más amigables:\n" + "\n".join(
            f"{i+1}. {u} (Confianza: {c})"
            for i, (u, c) in enumerate(top_list)
        )

        await ctx.send(mensaje)
