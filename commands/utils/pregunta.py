from twitchio.ext import commands
import asyncio
import random
from openai import OpenAI
from datetime import datetime
import os
import json

# Cargar config
with open("config.json", "r", encoding="utf-8") as f:
    config = json.load(f)

RESPUESTAS_FALLBACK = [
    "ahora mismo estoy más lento que mi conexión a Internet en 1998.",
    "mi cerebro está en mantenimiento. Intenta más tarde.",
    "incluso yo tengo mis límites. Prueba en un rato."
]

def generar_contexto_usuario(usuarios, user):
    return usuarios.get(user, {}).get("respuestas", [])

def agregar_a_memoria(user, campo, valor, usuarios):
    if user not in usuarios:
        usuarios[user] = {}
    if campo not in usuarios[user]:
        usuarios[user][campo] = []
    usuarios[user][campo].append(valor)
    return usuarios

class Pregunta(commands.Cog):

    def __init__(self, bot, memoria):
        self.bot = bot
        self.memoria = memoria
        self.usuarios = self.memoria.users if hasattr(self.memoria, "users") else {}

        # Inicializar cliente OpenAI
        api_key = os.getenv("OPENAI_API_KEY") or config.get("openai", {}).get("api_key")
        if not api_key:
            raise ValueError("❌ No se encontró la API key de OpenAI. Defínela en config.json o en la variable de entorno OPENAI_API_KEY")
        self.client_openai = OpenAI(api_key=api_key)

    @commands.command(name="pregunta")
    async def pregunta_profunda(self, ctx: commands.Context, *, pregunta: str = None):
        """Responde preguntas más elaboradas"""
        user = ctx.author.name.lower()
        
        if not pregunta or not pregunta.strip():
            await ctx.send(f"@{user}, haz una pregunta, no solo digas 'pregunta'.")
            return
        
        prompt = f"""
Usuario: @{user}
Pregunta: {pregunta}

Responde como un bot de Twitch sarcástico pero informativo:
- Da una respuesta útil pero con humor
- Máximo 3 frases
- Si no sabes algo, admítelo de forma graciosa
- Incluye alguna referencia a videojuegos si es posible
- Sé más elaborado que con el comando !oye
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
            self.usuarios = agregar_a_memoria(user, "respuestas", reply, self.usuarios)
            
        except Exception as e:
            print(f"Error en !pregunta: {e}")
            await ctx.send(f"@{user} Mi cerebro está más laggeado que un servidor de DayZ. Intenta luego.")
