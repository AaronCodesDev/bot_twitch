from twitchio.ext import commands
import random
from core.memory import Memory  # Ajusta según tu proyecto
from phrases.social.compare import compare_phrases  # Tus frases de comparación

class Comparar(commands.Cog):
    def __init__(self, bot, memoria: Memory):
        self.bot = bot
        self.memoria = memoria

    @commands.command(name='comparar') 
    async def comparar(self, ctx: commands.Context): 
        user = ctx.author.name.lower() 
        args = ctx.message.content.strip().split()  # Validar que pasen dos usuarios 

        if len(args) < 3:
            respuesta = f"@{user}, dime a quién comparar. Ej: !comparar piloto1 piloto2" 
            await ctx.send(respuesta) 

            # 🔹 Guardado seguro
            if hasattr(self.memoria, "add_mensaje"):
                self.memoria.add_mensaje(user, respuesta)
            if hasattr(self.memoria, "guardar_datos"):
                self.memoria.guardar_datos()
            return 
        
        jugador1 = args[1].lstrip("@").lower() 
        jugador2 = args[2].lstrip("@").lower() 
        
        if jugador1 == jugador2:
            respuesta = f"@{user}, comparar a {jugador1} consigo mismo es como comparar dos choques idénticos: inútil." 
            await ctx.send(respuesta) 

            # 🔹 Guardado seguro
            if hasattr(self.memoria, "add_mensaje"):
                self.memoria.add_mensaje(user, respuesta)
            if hasattr(self.memoria, "guardar_datos"):
                self.memoria.guardar_datos()
            return

        # Elegir ganador aleatoriamente 
        ganador = random.choice([jugador1, jugador2]) 
        perdedor = jugador1 if ganador == jugador2 else jugador2 
        frase = random.choice(compare_phrases).format(ganador=ganador, perdedor=perdedor) 

        await ctx.send(frase) 

        # 🔹 Guardado seguro
        if hasattr(self.memoria, "add_mensaje"):
            self.memoria.add_mensaje(user, frase)
        if hasattr(self.memoria, "guardar_datos"):
            self.memoria.guardar_datos()
