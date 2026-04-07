# commands/database/olvidarideas.py
from twitchio.ext import commands
from core.database import db
import asyncio
import random

CONFIRM_TIMEOUT = 30
SARCASTIC_MESSAGES = [
    "Vaya, parece que te da miedo perder estas brillantes ideas de tus viewers 😏",
    "Ups… parece que quieres que guarde todas sus ideas de tus viewers otra vez 🙄",
    "Ahí estás dudando… no, no voy a borrar nada todavía 😎",
    "Casi lo borraría, pero me dejaste pensando 😏"
]

class OlvidarIdeas(commands.Cog):

    def __init__(self, bot, memoria):
        self.bot = bot
        self.memoria = memoria
        self.confirmando = set()

    @commands.command(name="olvidarideas")
    async def borrar_ideas(self, ctx: commands.Context, *args):
        user = ctx.author.name.lower()

        if not (ctx.author.is_mod or ctx.author.is_broadcaster):
            await ctx.send(f"@{ctx.author.name} ❌ No tienes permiso para borrar las ideas.")
            return

        if user not in self.confirmando or not args:
            self.confirmando.add(user)
            await ctx.send(
                f"@{ctx.author.name} ⚠️ Esto borrará **todas las ideas del sorteo**. "
                f"Escribe `!olvidarideas CONFIRMAR` en los próximos {CONFIRM_TIMEOUT} segundos para confirmar."
            )
            await asyncio.sleep(CONFIRM_TIMEOUT)
            if user in self.confirmando:
                self.confirmando.remove(user)
                await ctx.send(f"@{ctx.author.name} {random.choice(SARCASTIC_MESSAGES)}")
            return

        if args[0].upper() == "CONFIRMAR" and user in self.confirmando:
            db.clear_ideas()
            self.confirmando.remove(user)
            await ctx.send(
                f"🗑️ Todas las ideas del sorteo han sido eliminadas por @{ctx.author.name}. "
                "Memoria formateada. Mentes en blanco. Café infinito necesario ☕😈"
            )
        else:
            await ctx.send(f"@{ctx.author.name}, la confirmación no es válida. Debes escribir `CONFIRMAR`.")