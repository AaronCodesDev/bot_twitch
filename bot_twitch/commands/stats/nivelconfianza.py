# commands/stats/nivelconfianza.py
from twitchio.ext import commands
from core.database import db

class NivelConfianza(commands.Cog):
    def __init__(self, bot, memoria):
        self.bot = bot
        self.memoria = memoria

    @commands.command(name="nivelconfianza")
    async def mostrar_niveles_confianza(self, ctx: commands.Context):
        mensaje = (
            "📊 Niveles de confianza: "
            "🔴 0-500: Antipático | "
            "🟡 501-999: Neutral | "
            "🟢 1000+: Amigable | "
            "Usa !confianza <usuario> para ver su nivel."
        )
        await ctx.send(mensaje)

    @commands.command(name="addconfianza")
    async def add_confianza(self, ctx: commands.Context, usuario: str = None, cantidad: str = None):
        if not (ctx.author.is_mod or ctx.author.is_broadcaster):
            await ctx.send(f"@{ctx.author.name}, no tienes permiso.")
            return

        if not usuario or not cantidad:
            await ctx.send("❓ Uso: !addconfianza <usuario> <cantidad>")
            return

        if not cantidad.isdigit():
            await ctx.send("❌ La cantidad debe ser un número.")
            return

        usuario = usuario.lstrip("@").lower()
        valor = int(cantidad)
        db.add_confianza(usuario, valor)
        nueva = db.get_confianza(usuario)
        await ctx.send(f"✅ +{valor} confianza a @{usuario} . Total: {nueva}")

    @commands.command(name="remconfianza")
    async def remove_confianza(self, ctx: commands.Context, usuario: str = None, cantidad: str = None):
        if not (ctx.author.is_mod or ctx.author.is_broadcaster):
            await ctx.send(f"@{ctx.author.name}, no tienes permiso.")
            return

        if not usuario or not cantidad:
            await ctx.send("❓ Uso: !remconfianza <usuario> <cantidad>")
            return

        if not cantidad.isdigit():
            await ctx.send("❌ La cantidad debe ser un número.")
            return

        usuario = usuario.lstrip("@").lower()
        valor = int(cantidad)
        db.add_confianza(usuario, -valor)
        nueva = db.get_confianza(usuario)
        await ctx.send(f"✅ -{valor} confianza a @{usuario}. Total: {nueva}")