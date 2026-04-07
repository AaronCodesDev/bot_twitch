# commands/customs/commands.py
from twitchio.ext import commands
from core.database import db

class CustomCommands(commands.Cog):

    def __init__(self, bot, memory, config=None):
        self.bot = bot
        self.memory = memory
        self.admin_list = [u.lower() for u in (config.get("admin_users", []) if config else [])]

    @commands.command(name="addcomando")
    async def add_comando(self, ctx: commands.Context, nombre: str = None, *, texto: str = None):
        if ctx.author.name.lower() not in self.admin_list:
            await ctx.send(f"❌ {ctx.author.name}, no tienes permiso.")
            return
        if not nombre or not texto:
            await ctx.send("❓ Uso: !addcomando [nombre] [texto]")
            return
        nombre = nombre.lower().replace("!", "")
        db.save_command(nombre, texto, creado_by=ctx.author.name.lower())
        await ctx.send(f"✅ Comando !{nombre} guardado correctamente.")

    @commands.command(name="delcomando")
    async def del_comando(self, ctx: commands.Context, nombre: str = None):
        if ctx.author.name.lower() not in self.admin_list:
            return
        if not nombre:
            return
        nombre = nombre.lower().replace("!", "")
        if db.get_command(nombre):
            db.delete_command(nombre)
            await ctx.send(f"🗑️ !{nombre} eliminado.")
        else:
            await ctx.send("❌ Ese comando no existe.")
            
    @commands.command(name="editcomando")
    async def edit_comando(self, ctx: commands.Context, nombre: str = None, *, texto: str = None):
        if ctx.author.name.lower() not in self.admin_list:
            await ctx.send(f"❌ {ctx.author.name}, no tienes permiso.")
            return
        if not nombre or not texto:
            await ctx.send("❓ Uso: !editcomando [nombre] [nuevo texto]")
            return
        nombre = nombre.lower().replace("!", "")
        if db.get_command(nombre):
            db.save_command(nombre, texto, creado_by=ctx.author.name.lower())
            await ctx.send(f"✅ Comando !{nombre} actualizado.")
        else:
            await ctx.send(f"❌ El comando !{nombre} no existe. Usa !addcomando para crearlo.")        

    @commands.command(name="listcomandos")
    async def list_comandos(self, ctx: commands.Context):
        comandos = db.get_all_commands()
        if not comandos:
            await ctx.send("No hay comandos personalizados.")
            return
        lista = ", ".join([f"!{c['comando']}" for c in comandos])
        await ctx.send(f"📜 Comandos: {lista}")