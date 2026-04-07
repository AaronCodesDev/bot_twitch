# commands/stats/nivel.py
from twitchio.ext import commands
from core.database import db
from datetime import datetime, timezone

class Nivel(commands.Cog):

    def __init__(self, bot, memoria):
        self.bot = bot
        self.memoria = memoria

    @commands.command(name="nivel")
    async def nivel_usuario(self, ctx: commands.Context):
        user = ctx.author.name.lower()

        sub = db.get_subscriber(user)
        favorito = db.get_favorito(user)

        if sub:
            nivel = "suscriptor"
            icono = "👑"
            extra = ""
        elif favorito:
            nivel = "favorito"
            icono = "💙"
            fecha_str = favorito.get("creado_at")
            dias = 0
            if fecha_str:
                try:
                    fecha = datetime.fromisoformat(fecha_str)
                    if fecha.tzinfo is None:
                        fecha = fecha.replace(tzinfo=timezone.utc)
                    dias = (datetime.now(timezone.utc) - fecha).days
                except:
                    pass
            extra = f" desde hace {dias} días" if dias else ""
        else:
            nivel = "normal"
            icono = "😏"
            extra = ""

        mensaje = f"@{user}, eres {nivel.upper()} {icono}{extra}"
        await ctx.send(mensaje)
        db.add_frase(user, mensaje, confianza=0)

    @commands.command(name="favorito")
    async def favorito(self, ctx: commands.Context, usuario: str = None):
        if not (ctx.author.is_mod or ctx.author.is_broadcaster):
            await ctx.send(f"@{ctx.author.name}, no tienes permiso.")
            return
        if not usuario:
            await ctx.send(f"@{ctx.author.name}, indica un usuario.")
            return

        usuario = usuario.lstrip("@").lower()
        db.save_favorito(usuario, usuario)
        await ctx.send(f"{usuario} ahora es FAVORITO 💙")

    @commands.command(name="unfavorito")
    async def unfavorito(self, ctx: commands.Context, usuario: str = None):
        if not (ctx.author.is_mod or ctx.author.is_broadcaster):
            await ctx.send(f"@{ctx.author.name}, no tienes permiso.")
            return
        if not usuario:
            await ctx.send(f"@{ctx.author.name}, indica un usuario.")
            return

        usuario = usuario.lstrip("@").lower()
        if db.get_favorito(usuario):
            db.delete_favorito(usuario)
            await ctx.send(f"{usuario} ya NO es favorito 😏")
        else:
            await ctx.send(f"{usuario} no era favorito.")