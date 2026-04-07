from twitchio.ext import commands
from phrases.giveaways.fuel import fuel_phrases
import random

class Gasolina(commands.Cog):

    def __init__(self, bot, memoria):
        self.bot = bot
        self.memoria = memoria

    @commands.command(name="gasolina")
    async def gasolina(self, ctx: commands.Context):
        frase = random.choice(fuel_phrases)
        await ctx.send(frase)
    