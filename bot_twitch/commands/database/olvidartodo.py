# commands/database/olvidartodo.py
from twitchio.ext import commands
from core.database import db
from core.config import DB_PATH
import os
import asyncio
import random
import shutil
from datetime import datetime

CONFIRM_TIMEOUT = 30
SARCASTIC_MESSAGES = [
    "¿eh? parece que al final te da miedo perder mis recuerdos 😏",
    "bueno, supongo que me quedo con tus secretos un rato más… 🙄",
    "ves? al final quieres que guarde todo 😎",
    "estaba a punto de borrarlo todo, pero me dejaste dudando 😏"
]

class OlvidarTodo(commands.Cog):

    def __init__(self, bot, memoria, config):
        self.bot = bot
        self.memoria = memoria
        self.admin_list = [u.lower() for u in config.get("admin_users", [])]
        self.confirmando = set()

    @commands.command(name="olvidartodo")
    async def borrar_todos_los_usuarios(self, ctx: commands.Context, *args):
        user = ctx.author.name.lower()

        if user not in self.admin_list:
            await ctx.send(f"@{ctx.author.name}, no tienes poder aquí. 😏")
            return

        if user not in self.confirmando or not args:
            self.confirmando.add(user)
            await ctx.send(
                f"@{ctx.author.name}, ¡atención! Esto borrará **todos los usuarios, recuerdos y hechos**. "
                f"Para confirmar, escribe `!olvidartodo CONFIRMAR` en los próximos {CONFIRM_TIMEOUT} segundos."
            )
            await asyncio.sleep(CONFIRM_TIMEOUT)
            if user in self.confirmando:
                self.confirmando.remove(user)
                await ctx.send(f"@{ctx.author.name} {random.choice(SARCASTIC_MESSAGES)}")
            return

        if args[0].upper() == "CONFIRMAR" and user in self.confirmando:
            print(f"⚠️ {ctx.author.name} ha confirmado borrar todo. Iniciando proceso...")
            print(f"TODO BORRADO POR {ctx.author.name} A LAS {datetime.now().strftime('%Y-%m-%d %H:%M')}")

            # -------------------- BACKUP --------------------
            # Hacemos una copia de la DB entera, mucho más simple que antes
            backup_dir = os.path.join("data", "backup")
            os.makedirs(backup_dir, exist_ok=True)
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            backup_path = os.path.join(backup_dir, f"backup_{timestamp}.db")
            shutil.copy2(DB_PATH, backup_path)
            print(f"💾 Backup guardado en {backup_path}")

            # -------------------- BORRADO --------------------
            cursor = db._cursor()
            cursor.execute("DELETE FROM recuerdos")
            cursor.execute("DELETE FROM hechos")
            cursor.execute("DELETE FROM user_frases")
            cursor.execute("DELETE FROM user_profiles")
            cursor.execute("DELETE FROM favoritos")
            cursor.execute("DELETE FROM subscribers")
            db._commit()

            self.confirmando.remove(user)
            await ctx.send(
                f"🧠💣 Todo borrado por @{ctx.author.name}. "
                "Backup guardado. No preguntes dónde, confía."
            )
        else:
            await ctx.send(f"@{ctx.author.name}, la confirmación no es válida. Debes poner `CONFIRMAR`.")