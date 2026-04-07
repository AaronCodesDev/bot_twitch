# commands/utils/pregunta.py
from twitchio.ext import commands
from core.database import db
import asyncio
import os
import json
from openai import OpenAI

BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
CONFIG_PATH = os.path.join(BASE_DIR, "config.json")

with open(CONFIG_PATH, "r", encoding="utf-8") as f:
    config = json.load(f)

class Pregunta(commands.Cog):

    def __init__(self, bot, memoria):
        self.bot = bot
        self.memoria = memoria

        api_key = os.getenv("OPENAI_API_KEY") or config.get("openai", {}).get("api_key")
        if not api_key:
            raise ValueError("❌ No se encontró la API key de OpenAI.")
        self.client_openai = OpenAI(api_key=api_key)

    @commands.command(name="pregunta")
    async def pregunta_profunda(self, ctx: commands.Context, *, pregunta: str = None):
        user = ctx.author.name.lower()

        if not pregunta or not pregunta.strip():
            await ctx.send(f"@{user}, haz una pregunta, no solo digas 'pregunta'.")
            return

        frases = db.get_frases(user)
        recuerdos = db.get_recuerdos(user, max_items=3)
        contexto = frases + [r["texto"] for r in recuerdos]

        prompt = f"""
Usuario: @{user}
Contexto conocido: {contexto}
Pregunta: {pregunta}

Responde como un bot de Twitch sarcástico pero informativo:
- Da una respuesta útil pero con humor
- Máximo 3 frases
- Si no sabes algo, admítelo de forma graciosa
- Incluye alguna referencia a videojuegos si es posible
- PROHIBIDO hablar de política, religión o temas sensibles
- Enfócate en gaming, tecnología, cultura pop o temas neutrales
"""

        try:
            response = await asyncio.to_thread(
                self.client_openai.chat.completions.create,
                model="gpt-3.5-turbo",
                messages=[{"role": "user", "content": prompt}],
                max_tokens=120,
                temperature=0.7,
            )
            reply = response.choices[0].message.content.strip()
            await ctx.send(f"@{user} {reply}")
            db.log_command(user, "pregunta", input=pregunta, respuesta=reply)

        except Exception as e:
            print(f"Error en !pregunta: {e}")
            await ctx.send(f"@{user} Mi cerebro está más laggeado que un servidor de DayZ. Intenta luego.")