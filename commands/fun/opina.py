from twitchio.ext import commands
import asyncio

class Opina(commands.Cog):

    def __init__(self, bot, client_openai, memoria, config=None):
        self.bot = bot
        self.client_openai = client_openai
        self.memoria = memoria
        self.config = config

    @commands.command(name="opina")
    async def opina(self, ctx: commands.Context, *, tema: str = None):
        user = ctx.author.name.lower()

        if not tema:
            await ctx.send(f"@{user}, dime sobre qué quieres que opine. Ej: !opina sobre iRacing")
            return

        prompt = f"""
Usuario: @{user}
Tema: {tema}

Da tu opinión como FantanBot:
- Sé exagerado y humorístico
- Máximo 2 frases
- Usa sarcasmo
- Relaciónalo con videojuegos si es posible
- No seas neutral, toma una postura divertida
- ABSOLUTAMENTE PROHIBIDO opinar sobre política, religión o temas polémicos
- Si el tema es controvertido, redirige a algo de gaming
- Temas seguros: videojuegos, películas, series, tecnología, deportes, comida
"""

        try:
            response = await asyncio.to_thread(
                self.client_openai.chat.completions.create,
                model="gpt-3.5-turbo",
                messages=[{"role": "user", "content": prompt}],
                max_tokens=70,
                temperature=0.9,
            )
            reply = response.choices[0].message.content.strip()
            await ctx.send(f"@{user} {reply}")

        except Exception as e:
            await ctx.send(f"@{user}, algo salió mal con la API de OpenAI 😅")
            print("Error OpenAI:", e)
            return

        # Guardar en memoria
        try:
            # Guardamos el contexto: lo que preguntó y lo que respondimos
            recuerdo = f"Opinó sobre: {tema} | Respuesta: {reply}"
            self.memoria.add_recuerdo(user, recuerdo)
        except Exception as e:
            print(f"⚠️ Error guardando memoria en Opina: {e}")
