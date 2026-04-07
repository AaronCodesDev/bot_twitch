from twitchio.ext import commands
import random
from core.memory import Memory  # Ajusta según tu proyecto
from phrases.social.slogans import slogans_phrases  # Tus frases de slogans

class Lemas(commands.Cog):

    def __init__(self, bot, memoria: Memory):
        self.bot = bot
        self.memoria = memoria
    
    @commands.command(name="lemas") 
    async def lemas(self, ctx: commands.Context): 
        user = ctx.author.name.lower() 
        frase = random.choice(slogans_phrases) 

        await ctx.send(f"👉 {frase}") 

        # Guardamos la frase en memoria
        self.memoria.add_recuerdo(user, frase)
