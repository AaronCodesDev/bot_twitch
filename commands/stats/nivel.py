from twitchio.ext import commands
from datetime import datetime, timezone

class Nivel(commands.Cog):

    def __init__(self, bot, memoria):
        self.bot = bot
        self.memoria = memoria

    # ------------------ Nivel del usuario ------------------
    @commands.command(name="nivel")
    async def nivel_usuario(self, ctx: commands.Context):
        user = ctx.author.name.lower()

        # Sub (activo)
        if user in self.memoria.subs:
            nivel = "suscriptor"
            icono = "👑"
            extra = ""
        # Favorito
        elif user in self.memoria.favoritos:
            nivel = "favorito"
            icono = "💙"
            # Calcular días desde que es favorito
            fav_data = self.memoria.favoritos[user]
            fecha_str = fav_data.get("fecha")
            dias = 0
            if fecha_str:
                try:
                    fecha = datetime.fromisoformat(fecha_str)
                    delta = datetime.now(timezone.utc) - fecha
                    dias = delta.days
                except Exception:
                    pass
            extra = f" desde hace {dias} días" if dias else ""
        # Normal
        else:
            nivel = "normal"
            icono = "😏"
            extra = ""

        mensaje = f"@{user}, eres {nivel.upper()} {icono}{extra}"
        await ctx.send(mensaje)

        # Guardar la frase en Memory
        self.memoria.add_frase(user, mensaje, confianza=0)

    # ------------------ Añadir favorito ------------------
    @commands.command(name="favorito")
    async def favorito(self, ctx: commands.Context, usuario: str):
        if not (ctx.author.is_mod or ctx.author.is_broadcaster):
            await ctx.send(f"@{ctx.author.name}, no tienes permiso.")
            return

        usuario = usuario.lower()
        self.memoria.favoritos[usuario] = {"fecha": datetime.now(timezone.utc).isoformat()}
        self.memoria._save(self.memoria.favoritos_file, self.memoria.favoritos)
        await ctx.send(f"{usuario} ahora es FAVORITO 💙")

    # ------------------ Quitar favorito ------------------
    @commands.command(name="unfavorito")
    async def unfavorito(self, ctx: commands.Context, usuario: str):
        if not (ctx.author.is_mod or ctx.author.is_broadcaster):
            await ctx.send(f"@{ctx.author.name}, no tienes permiso.")
            return

        usuario = usuario.lower()
        if usuario in self.memoria.favoritos:
            del self.memoria.favoritos[usuario]
            self.memoria._save(self.memoria.favoritos_file, self.memoria.favoritos)
        await ctx.send(f"{usuario} ya NO es favorito 😏")
