from twitchio.ext import commands
import random
from core.memory import Memory  # Ajusta según tu proyecto
from phrases.social.ban import ban_phrases  # Tus frases de ban

class Ban(commands.Cog):

    def __init__(self, bot, memoria: Memory):
        self.bot = bot
        self.memoria = memoria
        
    @commands.command(name="ban") 
    async def ban(self, ctx: commands.Context, *, objetivo: str = None): 
        user = ctx.author.name.lower() 
        
        if not objetivo: 
            await ctx.send(f"@{user}, dime a quién banear. Ej: !ban @usuario") 
            return 

        frase_ban = random.choice(ban_phrases) 
        respuesta = frase_ban.replace('{objetivo}', objetivo) 

        await ctx.send(f'@{user}, {respuesta}') 

        # Guardamos la respuesta en memoria
        self.memoria.add_recuerdo(user, respuesta)
