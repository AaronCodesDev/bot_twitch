from twitchio.ext import commands
from datetime import datetime
import json
import os

IDEAS_FILE = "data/save/ideas_sorteo.json"

def cargar_ideas():
    if not os.path.exists(IDEAS_FILE):
        return []
    with open(IDEAS_FILE, "r", encoding="utf-8") as f:
        return json.load(f)

class Ideas(commands.Cog):

    def __init__(self, bot, memoria):
        self.bot = bot
        self.memoria = memoria

    @commands.command(name="ideas")
    async def listar_ideas(self, ctx: commands.Context):
        # Solo mods o broadcaster
        if not (ctx.author.is_mod or ctx.author.is_broadcaster):
            await ctx.send("❌ No tienes permiso para ver las ideas.")
            return

        ideas = cargar_ideas()

        if not ideas:
            await ctx.send("📭 No hay ideas registradas todavía.")
            return

        ultimas = ideas[-5:]  # últimas 5 ideas
        mensaje = "💡 Últimas ideas de premios:\n"

        mensaje += " | ".join(
            [f"{i['usuario']}: {i['idea'][:40]}" for i in ultimas]
        )

        await ctx.send(mensaje)
