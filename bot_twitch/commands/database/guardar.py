# commands/database/guardar.py
from twitchio.ext import commands
from core.database import db
from phrases.bot.saved import saved_phrases
import random

class Guardar(commands.Cog):

    def __init__(self, bot, memoria):
        self.bot = bot
        self.memoria = memoria

    @commands.command(name="guardar")
    async def guardar_memoria(self, ctx: commands.Context):
        if not (ctx.author.is_mod or ctx.author.is_broadcaster):
            await ctx.send("❌ No tienes permisos para hacer eso.")
            return

        await ctx.send(random.choice(saved_phrases))
        print(f"💾 Confirmación de guardado por {ctx.author.name}")