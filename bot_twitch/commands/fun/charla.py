# commands/fun/charla.py
from twitchio.ext import commands
from core.database import db
import asyncio
import random
import os
import json
from openai import OpenAI

BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
CONFIG_PATH = os.path.join(BASE_DIR, "config.json")

with open(CONFIG_PATH, "r", encoding="utf-8") as f:
    config = json.load(f)

RESPUESTAS_FALLBACK = [
    "ahora mismo estoy más lento que mi conexión a Internet en 1998.",
    "mi cerebro está en mantenimiento. Intenta más tarde.",
    "incluso yo tengo mis límites. Prueba en un rato."
]

class Charla(commands.Cog):

    def __init__(self, bot, memoria):
        self.bot = bot
        self.memoria = memoria

        api_key = os.getenv("OPENAI_API_KEY") or config.get("openai", {}).get("api_key")
        if not api_key:
            raise ValueError("❌ No se encontró la API key de OpenAI.")
        self.client_openai = OpenAI(api_key=api_key)

    @commands.command(name="charla", aliases=["habla", "conversa"])
    async def charla(self, ctx: commands.Context, *, mensaje: str = None):
        user = ctx.author.name.lower()

        if not mensaje or not mensaje.strip():
            await ctx.send(f"@{user}, si quieres charlar, dime algo más que mi nombre.")
            return

        frases = db.get_frases(user)
        recuerdos = db.get_recuerdos(user, max_items=3)
        contexto = frases + [r["texto"] for r in recuerdos]

        system_message = f"""
        Eres FantanBot, un bot de Twitch sarcástico y ocurrente.
        Características:
        - Fan de iRacing, shooters y supervivencia
        - Responde con humor negro y sarcasmo
        - Máximo 2 frases cortas
        - Sé natural y desenfadado
        - Haz referencias a videojuegos cuando sea posible
        - PROHIBIDO hablar de política, religión o temas controvertidos

        Contexto del usuario {user}:
        {contexto}

        Responde de forma conversacional, como si estuvieras en un chat de Twitch.
        """

        try:
            response = await asyncio.to_thread(
                self.client_openai.chat.completions.create,
                model="gpt-3.5-turbo",
                messages=[
                    {"role": "system", "content": system_message},
                    {"role": "user", "content": f"@{user} dice: {mensaje}"},
                ],
                max_tokens=80,
                temperature=0.8,
            )
            reply = response.choices[0].message.content.strip()
            await ctx.send(f"@{user} {reply}")
            db.log_command(user, "charla", input=mensaje, respuesta=reply)

        except Exception as e:
            print(f"Error en charla: {e}")
            await ctx.send(f"@{user} {random.choice(RESPUESTAS_FALLBACK)}")