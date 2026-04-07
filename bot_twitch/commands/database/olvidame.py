# commands/database/olvidame.py
from twitchio.ext import commands
from core.database import db
import asyncio

CONFIRM_KEYWORD = "CONFIRMAR"
CONFIRM_TIMEOUT = 30

class Olvidame(commands.Cog):

    def __init__(self, bot, memoria):
        self.bot = bot
        self.memoria = memoria
        self.confirmando = {}

    @commands.command(name="olvidame")
    async def olvidarme(self, ctx: commands.Context, *args):
        user = ctx.author.name.lower()

        if user in self.confirmando:
            if args and args[0].upper() == CONFIRM_KEYWORD:
                # Borrar todos los datos del usuario de la DB
                db._cursor().execute("DELETE FROM recuerdos WHERE username=?", (user,))
                db._cursor().execute("DELETE FROM user_frases WHERE username=?", (user,))
                db._cursor().execute("DELETE FROM user_profiles WHERE username=?", (user,))
                db._commit()
                self.confirmando[user]["task"].cancel()
                del self.confirmando[user]
                await ctx.send(f"@{user}, tus datos han sido olvidados 😢")
            else:
                await ctx.send(f"@{user}, para confirmar escribe !olvidame {CONFIRM_KEYWORD}")
            return

        perfil = db.get_confianza(user)
        recuerdos = db.get_recuerdos(user, max_items=1)

        if perfil or recuerdos:
            self.confirmando[user] = {"task": asyncio.create_task(self.expirar_confirmacion(ctx, user))}
            await ctx.send(
                f"@{user}, esto borrará todos tus datos. "
                f"Para confirmar escribe !olvidame {CONFIRM_KEYWORD} "
                f"en los próximos {CONFIRM_TIMEOUT} segundos."
            )
        else:
            await ctx.send(f"@{user}, no hay nada que olvidar.")

    async def expirar_confirmacion(self, ctx: commands.Context, user: str):
        try:
            await asyncio.sleep(CONFIRM_TIMEOUT)
            if user in self.confirmando:
                await ctx.send(f"@{user}, ves si es que al final quieres que me acuerde de ti… 😏")
                del self.confirmando[user]
        except asyncio.CancelledError:
            pass