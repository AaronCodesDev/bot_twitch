# commands/database/idea.py
from twitchio.ext import commands
from core.database import db
import random

RESPUESTAS_IDEA = [
    "💡 Idea registrada. Luego la evaluaré… con café y mala leche ☕😈",
    "📝 Anotado. No prometo que sea buena idea, pero ahí queda 😏",
    "🧠 Guardado. Si gana el sorteo será por suerte, no por mérito 🎲",
    "✅ Registrado. Spoiler: probablemente no gane 😎",
    "📌 Idea apuntada. El premio sube con las subs… así que reza 🙏",
    "💾 Guardado en mi memoria… que tampoco es muy fiable 😅",
    "🎯 Idea anotada. Compite con las demás… buena suerte, la vas a necesitar 😈",
    "📋 Registrado. No sé si es buena idea, pero el café ya está hecho ☕",
    "🗂️ Apuntado. Si ganas será un milagro… pero los milagros existen 😏",
    "✍️ Guardado. Hay mejores ideas, pero la tuya tiene personalidad 🙄",
]

RESPUESTAS_SIN_IDEA = [
    "no soy adivino, escribe algo… !idea <tu idea> 📉 | El premio sube con las subs. Sin subs = premio triste.",
    "¿una idea vacía? Creativo, pero no cuenta. Usa !idea <tu idea aquí> 😏",
    "necesito texto, no silencio. !idea <tu idea> o te quedas sin participar 😈",
    "el comando es !idea <tu idea>… no !idea y ya. Inténtalo de nuevo 🙄",
    "sin idea no hay sorteo. Escribe algo con !idea <tu idea> ☕",
    "¿pensabas que iba a adivinar tu idea? Soy un bot, no un psíquico. !idea <tu idea> 🔮",
    "idea en blanco… como tu estrategia. Usa !idea <tu idea aquí> 😂",
    "error 404: idea no encontrada. Intenta con !idea <tu idea> 💻",
    "participar requiere un mínimo de esfuerzo. !idea <tu idea> y listo 😎",
    "eso no es una idea, eso es aire. Escribe algo con !idea <tu idea> 🌬️",
]

class Idea(commands.Cog):

    def __init__(self, bot, memoria):
        self.bot = bot
        self.memoria = memoria

    @commands.command(name="idea")
    async def idea_premio(self, ctx: commands.Context, *, idea: str = None):
        user = ctx.author.name.lower()

        if not idea or not idea.strip():
            await ctx.send(f"@{user}, {random.choice(RESPUESTAS_SIN_IDEA)}")
            return

        db.save_idea(usuario=user, idea=idea.strip())
        await ctx.send(f"@{user} {random.choice(RESPUESTAS_IDEA)}")