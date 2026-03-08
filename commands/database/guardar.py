from twitchio.ext import commands
import random
import json
import os

FAVORITOS_FILE = "data/save/favoritos.json"
SUBS_FILE = "data/subs/subscriptores_activos.json"

saved_phrases = [
    "💾 Guardado. Sorprendentemente, sin romper nada.",
    "✅ Datos a salvo… por ahora.",
    "📦 Todo guardado. El disco sigue vivo.",
    "🧠 Memoria actualizada. Milagro.",
    "🔐 Datos guardados. Nadie preguntó, pero ahí están.",
    "📁 Archivos guardados. Sí, de verdad.",
    "⚙️ Guardado completado. No lo repitas por si acaso.",
    "✨ Todo listo. No toques nada más.",
    "📌 Datos registrados. Intenta no borrarlos.",
    "🚀 Guardado hecho. El bot sobrevive otro día."
]

def guardar_favoritos(favoritos):
    os.makedirs(os.path.dirname(FAVORITOS_FILE), exist_ok=True)
    with open(FAVORITOS_FILE, 'w', encoding='utf-8') as f:
        json.dump(favoritos, f, indent=4, ensure_ascii=False)

def guardar_suscriptores(subs):
    os.makedirs(os.path.dirname(SUBS_FILE), exist_ok=True)
    with open(SUBS_FILE, 'w', encoding='utf-8') as f:
        json.dump(subs, f, indent=4, ensure_ascii=False)

class Guardar(commands.Cog):

    def __init__(self, bot, memoria):
        self.bot = bot
        self.memoria = memoria

    @commands.command(name="guardar")
    async def guardar_memoria(self, ctx: commands.Context):

        if not (ctx.author.is_mod or ctx.author.is_broadcaster):
            await ctx.send("❌ No tienes permisos para hacer eso.")
            return

        guardar_favoritos(self.memoria.favoritos)
        guardar_suscriptores(self.memoria.subs)

        await ctx.send(random.choice(saved_phrases))
        print(f"💾 Datos globales guardados manualmente por {ctx.author.name}")
