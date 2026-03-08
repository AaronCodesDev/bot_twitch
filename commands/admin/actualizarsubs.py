from twitchio.ext import commands
from bot import importar_subs_al_arrancar  # IMPORTANTE: importar la función global

class ActualizarSubs(commands.Cog):

    def __init__(self, bot, memoria):
        self.bot = bot
        self.memoria = memoria

    @commands.command(name="actualizarsubs")
    async def actualizarsubs(self, ctx: commands.Context):
        # Solo mods o broadcaster
        if not (ctx.author.is_mod or ctx.author.is_broadcaster):
            return

        await ctx.send("🔄 Llamando a Twitch… si falla no es culpa mía, es de Amazon.")

        try:
            # Llamada al método del bot
            exito = await self.bot.actualizar_csv_desde_twitch()
        except Exception as e:
            print(f"❌ Error actualizando subs: {e}")
            await ctx.send("❌ Error interno al conectar con Twitch.")
            return

        if exito:
            # Llamada CORRECTA a la función global
            importar_subs_al_arrancar()
            await ctx.send("✅ Lista de suscriptores sincronizada correctamente.")
        else:
            await ctx.send("❌ Hubo un error al conectar con la API de Twitch.")
