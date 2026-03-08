from twitchio.ext import commands


class Confianza(commands.Cog):

    def __init__(self, bot, memoria):
        self.bot = bot
        self.memoria = memoria

    # --- Cálculo de nivel de confianza ---
    def _nivel_confianza(self, confianza: int) -> str:
        if confianza >= 1000:
            return "🟢 Amigable"
        elif confianza >= 501:
            return "🟡 Neutral"
        return "🔴 Antipático"

    @commands.command(name='confianza')
    async def confianza(self, ctx: commands.Context, target_user: str = None):
        autor = ctx.author.name.lower()

        # Usuario objetivo
        if not target_user or not target_user.strip():
            usuario = autor
        else:
            usuario = target_user.lstrip('@').lower()

        # Protección del bot
        if usuario == "bot_fantan":
            await ctx.send(f"@{ctx.author.name}, de ese bot no hablo... 🤬🤐")
            return

        # Cargar datos
        data = self.memoria._load_user(usuario)
        if not data:
            await ctx.send(f"@{ctx.author.name}, no tengo datos de @{usuario}.")
            return

        confianza = data.get("confianza", 0)
        nivel = self._nivel_confianza(confianza)

        # Respuesta
        if usuario == autor:
            await ctx.send(
                f"@{ctx.author.name}, tu confianza es {confianza} → {nivel} 😏"
            )
        else:
            await ctx.send(
                f"@{ctx.author.name}, @{usuario} tiene {confianza} de confianza → {nivel} 😏"
            )
