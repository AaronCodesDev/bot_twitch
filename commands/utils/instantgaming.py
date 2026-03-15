import random
import asyncio
from twitchio.ext import commands
from phrases.social.instantgaming import instant_gaming_phrases

class InstantGaming(commands.Cog):
    def __init__(self, bot, config, memory=None):
        self.bot = bot
        self.config = config
        self.memory = memory
        # Solo creamos la tarea de envío periódico, no enviamos nada al inicio
        self.bot.loop.create_task(self.send_promo_periodically())

    @commands.command(name="instantgaming")
    async def instantgaming(self, ctx: commands.Context):
        """Envía una frase random de Instant Gaming al comando"""
        frase = random.choice(instant_gaming_phrases)
        await ctx.send(frase)

    async def send_promo_periodically(self):
        """Envía automáticamente frases cada 5 minutos"""
        
        # Obtener el canal desde config.json
        channel_name = self.config.get("twitch", {}).get("channel")
        if not channel_name:
            print("❌ Error: twitch_channel no está definido en config.json")
            return

        while True:
            # Espera 5 minutos antes de enviar la primera frase
            await asyncio.sleep(900)

            channel = None
            # Espera hasta que el canal esté disponible en connected_channels
            while channel is None:
                channel = self.bot.get_channel(channel_name)
                if channel is None:
                    await asyncio.sleep(1)  # reintenta hasta que el canal exista

            # Enviar frase
            frase = random.choice(instant_gaming_phrases)
            await channel.send(frase)

