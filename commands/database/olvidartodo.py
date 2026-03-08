from twitchio.ext import commands
import os
import asyncio
import random
from datetime import datetime
import shutil

CONFIRM_TIMEOUT = 30  # segundos para confirmar
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
        self.confirmando = set()  # admins que están confirmando

    @commands.command(name="olvidartodo")
    async def borrar_todos_los_usuarios(self, ctx: commands.Context, *args):
        user = ctx.author.name.lower()

        if user not in self.admin_list:
            await ctx.send(f"@{ctx.author.name}, no tienes poder aquí. 😏")
            return

        # Si no se pasó argumento de confirmación
        if user not in self.confirmando or not args:
            self.confirmando.add(user)
            await ctx.send(
                f"@{ctx.author.name}, ¡atención! Esto borrará **todos los usuarios, recuerdos y hechos**. "
                "Para confirmar, escribe `!olvidartodo CONFIRMAR` en los próximos 30 segundos."
            )
            
            # Espera 30 segundos para confirmación
            await asyncio.sleep(CONFIRM_TIMEOUT)
            if user in self.confirmando:
                self.confirmando.remove(user)
                await ctx.send(f"@{ctx.author.name} {random.choice(SARCASTIC_MESSAGES)}")
            return

        # Confirmación
        if args[0].upper() == "CONFIRMAR" and user in self.confirmando:
            
            print(f"⚠️ {ctx.author.name} ha confirmado borrar todo. Iniciando proceso...")
            print("Esto puede tardar un poco dependiendo de la cantidad de datos. ¡Paciencia! ⚠️")
            print(f"TODO BORRADO POR {ctx.author.name} A LAS {datetime.now().strftime('%Y-%m-%d %H:%M')}")

            # -------------------- BACKUP --------------------
            backup_dir = os.path.join("data", "backup")
            os.makedirs(backup_dir, exist_ok=True)
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            backup_path = os.path.join(backup_dir, f"backup_{timestamp}")
            os.makedirs(backup_path, exist_ok=True)

            # Guardar usuarios
            if os.path.exists(self.memoria.users_dir):
                shutil.copytree(self.memoria.users_dir, os.path.join(backup_path, "users"))

            # Guardar archivos individuales
            for archivo in [self.memoria.hechos_file, self.memoria.recuerdos_file, 
                            self.memoria.favoritos_file, self.memoria.subs_file]:
                if os.path.exists(archivo):
                    shutil.copy2(archivo, backup_path)
            
            # -------------------- BORRADO --------------------
            # 1️⃣ Borrar todos los archivos de usuarios
            if os.path.exists(self.memoria.users_dir):
                for archivo in os.listdir(self.memoria.users_dir):
                    if archivo.endswith(".json"):
                        os.remove(os.path.join(self.memoria.users_dir, archivo))

            # 2️⃣ Borrar todos los hechos (!recuerda)
            if os.path.exists(self.memoria.hechos_file):
                os.remove(self.memoria.hechos_file)
            self.memoria.hechos = []

            # 3️⃣ Borrar todos los recuerdos
            if os.path.exists(self.memoria.recuerdos_file):
                os.remove(self.memoria.recuerdos_file)
            self.memoria.recuerdos_global = {}

            # 4️⃣ Limpiar favoritos y subs
            self.memoria.favoritos = {}
            self.memoria.subs = {}
            self.memoria._save(self.memoria.favoritos_file, self.memoria.favoritos)
            self.memoria._save(self.memoria.subs_file, self.memoria.subs)

            self.confirmando.remove(user)
            await ctx.send(f"🧠💣 Todos borrado por @{ctx.author.name} "
                           f"Backup guardado. No preguntes dónde, confía.")
        else:
            await ctx.send(f"@{ctx.author.name}, la confirmación no es válida. Debes poner `CONFIRMAR`.")
