from twitchio.ext import commands
from phrases.social.cockpit import cockpit_message, cockpit_tip

class Cockpit(commands.Cog):
    
    def __init__(self, bot, memoria):
        self.bot = bot
        self.memoria = memoria
        
    @commands.command()
    async def cockpit(self, ctx: commands.Context):
        user = ctx.author.name.lower()
        es_mod_o_broadcaster = ctx.author.is_mod or ctx.author.is_broadcaster

        await ctx.send(cockpit_message)

        if es_mod_o_broadcaster:
            await ctx.send(cockpit_tip)
    