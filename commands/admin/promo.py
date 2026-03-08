from twitchio.ext import commands
import random
from phrases.social.promo import promo_phrases

class Promo(commands.Cog):

    def __init__(self, bot, memoria):
        self.bot = bot
        self.memoria = memoria

    @commands.command(name='promo', aliases=['so']) 
    async def promo(self, ctx: commands.Context, targetUser: str = None): 

        if not (ctx.author.is_mod or ctx.author.is_broadcaster): 
            await ctx.send(f"@{ctx.author.name}, no tienes permiso para promocionar.") 
            return 

        if not targetUser: 
            await ctx.send(f"@{ctx.author.name}, especifica a quién promocionar. Ej: !promo usuario") 
            return 

        frase = random.choice(promo_phrases)

        respuesta = frase.format(
            user=targetUser,
            user_lower=targetUser.lower()
        )

        await ctx.send(respuesta)
