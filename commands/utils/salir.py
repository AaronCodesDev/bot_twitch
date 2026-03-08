from twitchio.ext import commands
import random
import aiohttp
from phrases.bot.exit import exit_phrases  # Lista de frases de despedida

class Salir(commands.Cog):

    def __init__(self, bot, memoria):
        self.bot = bot
        self.memoria = memoria  # memoria del bot

    @commands.command(name="salir")
    async def salir(self, ctx: commands.Context):
        """Comando para cerrar el bot completamente"""
        user = ctx.author.name.lower()
        
        # Solo mods o broadcaster
        if not (ctx.author.is_mod or ctx.author.is_broadcaster):
            await ctx.send(f"@{user}, no tienes permiso para cerrar el bot.")
            return
        
        # Frase de despedida aleatoria
        frase_despedida = random.choice(exit_phrases)
        await ctx.send(f"@{user} {frase_despedida}")
        
        # Guardar todos los datos manualmente
        try:
            print("💾 Guardando datos antes de cerrar...")
            # Guardar hechos
            self.memoria._save(self.memoria.hechos_file, self.memoria.hechos)
            # Guardar recuerdos globales
            self.memoria._save(self.memoria.recuerdos_file, self.memoria.recuerdos_global)
            # Guardar suscriptores activos
            self.memoria._save(self.memoria.subs_file, self.memoria.subs)
            # Guardar favoritos
            self.memoria._save(self.memoria.favoritos_file, self.memoria.favoritos)
            print("✅ Datos guardados.")
        except Exception as e:
            print(f"⚠️ Error guardando memoria: {e}")

        # Cerrar cualquier sesión HTTP abierta
        try:
            print("🔒 Cerrando sesiones HTTP abiertas...")
            await aiohttp.ClientSession().close()
            print("✅ Sesiones HTTP cerradas.")
        except Exception:
            pass  # Si no hay sesiones abiertas, ignora

        # Cerrar el bot
        print("🔒 Cerrando bot...")
        await self.bot.close()
