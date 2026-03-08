from twitchio.ext import commands
import random
from datetime import datetime
import json
import os

IDEAS_FILE = "data/save/ideas_sorteo.json"

def cargar_ideas():
    if not os.path.exists(IDEAS_FILE):
        return []
    with open(IDEAS_FILE, "r", encoding="utf-8") as f:
        return json.load(f)

def guardar_ideas(ideas):
    os.makedirs(os.path.dirname(IDEAS_FILE), exist_ok=True)
    with open(IDEAS_FILE, "w", encoding="utf-8") as f:
        json.dump(ideas, f, indent=4, ensure_ascii=False)

class Idea(commands.Cog):

    def __init__(self, bot, memoria):
        self.bot = bot
        self.memoria = memoria

    @commands.command(name="idea")
    async def idea_premio(self, ctx: commands.Context, *, idea: str = None):
        user = ctx.author.name.lower()

        if not idea or not idea.strip():
            await ctx.send(
                f"@{user}, escribe la idea para el sorteo… "
                "no soy adivino 📉 | El premio sube con las subs del mes. "
                "Sin subs = premio triste."
            )
            return

        ideas = cargar_ideas()

        nueva_idea = {
            "usuario": user,
            "idea": idea.strip(),
            "fecha": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        }

        ideas.append(nueva_idea)
        guardar_ideas(ideas)

        await ctx.send(
            f"💡 Idea registrada, @{user}. "
            "Luego la evaluaré… con café y mala leche ☕😈"
        )
