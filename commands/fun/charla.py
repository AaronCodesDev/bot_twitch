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

# Fallback de respuestas si OpenAI falla
RESPUESTAS_FALLBACK = [
    "ahora mismo estoy más lento que mi conexión a Internet en 1998.",
    "mi cerebro está en mantenimiento. Intenta más tarde.",
    "incluso yo tengo mis límites. Prueba en un rato."
]

# Función de ejemplo para obtener contexto del usuario (tú ya la debes tener)
def generar_contexto_usuario(usuarios, user):
    return usuarios.get(user, {}).get("respuestas", [])

# Función de ejemplo para guardar en memoria (tú ya la debes tener)
def agregar_a_memoria(user, campo, valor, usuarios):
    if user not in usuarios:
        usuarios[user] = {}
    if campo not in usuarios[user]:
        usuarios[user][campo] = []
    usuarios[user][campo].append(valor)
    return usuarios

class Charla(commands.Cog):

    def __init__(self, bot, memoria):
        self.bot = bot
        self.memoria = memoria
        self.usuarios = self.memoria.users if hasattr(self.memoria, "users") else {}

        # Inicializar cliente OpenAI con API key de config o variable de entorno
        api_key = os.getenv("OPENAI_API_KEY") or config.get("openai", {}).get("api_key")
        if not api_key:
            raise ValueError("❌ No se encontró la API key de OpenAI. Defínela en config.json o en la variable de entorno OPENAI_API_KEY")
        self.client_openai = OpenAI(api_key=api_key)

    @commands.command(name="charla", aliases=["habla", "conversa"])
    async def charla(self, ctx: commands.Context, *, mensaje: str = None):
        """Comando para tener conversaciones naturales con el bot"""
        user = ctx.author.name.lower()
        
        if not mensaje or not mensaje.strip():
            await ctx.send(f"@{user}, si quieres charlar, dime algo más que mi nombre.")
            return

        # Obtener contexto personalizado del usuario
        contexto = generar_contexto_usuario(self.usuarios, user)
        
        system_message = f"""
        Eres FantanBot, un bot de Twitch sarcástico y ocurrente.
        Características:
        - Fan de iRacing, shooters y supervivencia
        - Responde con humor negro y sarcasmo
        - Máximo 2 frases cortas
        - Sé natural y desenfadado
        - Haz referencias a videojuegos cuando sea posible
        - PROHIBIDO hablar de política, religión o temas controvertidos
        - Mantén el enfoque en gaming, humor y temas livianos
        
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
            
            # Guardar en memoria
            self.usuarios = agregar_a_memoria(user, "respuestas", reply, self.usuarios)

        except Exception as e:
            print(f"Error en charla: {e}")
            fallback = random.choice(RESPUESTAS_FALLBACK)
            await ctx.send(f"@{user} {fallback}")
