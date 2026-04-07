from twitchio.ext import commands
from phrases.giveaways.raffle import raffle_phrases
import random

class Sorteo(commands.Cog):

    def __init__(self, bot, memoria):
        self.bot = bot
        self.memoria = memoria

    @commands.command(name="sorteo")
    async def sorteo(self, ctx: commands.Context):
        frase = random.choice(raffle_phrases)
        await ctx.send(frase)
    