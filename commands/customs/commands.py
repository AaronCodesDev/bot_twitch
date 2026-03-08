from twitchio.ext import commands
import json
import os

COMMANDS_FILE = "data/custom_commands/commands.json"

class CustomCommands(commands.Cog):
    """
    Cog para gestionar comandos personalizados desde Twitch.
    Permite agregar, eliminar y listar comandos dinámicos.
    """

    def __init__(self, bot, memory, config=None):
        self.bot = bot
        self.memory = memory
        self.admin_list = [u.lower() for u in config.get("admin_users", [])] if config else []
        self.custom_commands = self._load()  # Diccionario con los comandos cargados

    # ---------------- CARGAR COMANDOS ----------------
    def _load(self):
        if not os.path.exists(COMMANDS_FILE):
            # Crear carpeta y archivo vacío si no existe
            os.makedirs(os.path.dirname(COMMANDS_FILE), exist_ok=True)
            with open(COMMANDS_FILE, "w", encoding="utf-8") as f:
                json.dump({}, f, indent=4, ensure_ascii=False)
            return {}
        with open(COMMANDS_FILE, "r", encoding="utf-8") as f:
            try:
                return json.load(f)
            except json.JSONDecodeError:
                # Si el JSON está corrupto, reiniciar vacío
                return {}

    # ---------------- GUARDAR COMANDOS ----------------
    def _save(self):
        os.makedirs(os.path.dirname(COMMANDS_FILE), exist_ok=True)
        with open(COMMANDS_FILE, "w", encoding="utf-8") as f:
            json.dump(self.custom_commands, f, indent=4, ensure_ascii=False)

    # ---------------- AÑADIR COMANDO ----------------
    @commands.command(name="addcomando")
    async def add_comando(self, ctx: commands.Context, nombre: str, *, texto: str):
        if ctx.author.name.lower() not in self.admin_list:
            await ctx.send("❌ No tienes permisos para crear comandos.")
            return

        nombre = nombre.lower()
        if nombre in self.custom_commands:
            await ctx.send(f"⚠️ El comando `!{nombre}` ya existe.")
            return

        self.custom_commands[nombre] = texto
        self._save()
        await ctx.send(f"✅ Comando `!{nombre}` creado.")

    # ---------------- ELIMINAR COMANDO ----------------
    @commands.command(name="delcomando")
    async def del_comando(self, ctx: commands.Context, nombre: str):
        if ctx.author.name.lower() not in self.admin_list:
            await ctx.send("❌ No tienes permisos.")
            return

        nombre = nombre.lower()
        if nombre not in self.custom_commands:
            await ctx.send("❌ Ese comando no existe.")
            return

        del self.custom_commands[nombre]
        self._save()
        await ctx.send(f"🗑️ Comando `!{nombre}` eliminado.")

    # ---------------- LISTAR COMANDOS ----------------
    @commands.command(name="listcomandos")
    async def listar_comandos(self, ctx: commands.Context):
        if not self.custom_commands:
            await ctx.send("No hay comandos personalizados.")
            return

        lista = ", ".join(f"!{c}" for c in self.custom_commands.keys())
        await ctx.send(f"📜 Comandos disponibles: {lista}")

    # ---------------- EJECUTAR COMANDO ----------------
    async def ejecutar_comando(self, nombre, message):
        """
        Método auxiliar para ejecutar comandos dinámicos desde BotFantan.
        Reemplaza {user} por el nombre del autor.
        """
        nombre = nombre.lower()
        if nombre in self.custom_commands:
            respuesta = self.custom_commands[nombre].replace("{user}", message.author.name)
            await message.channel.send(respuesta)
