from twitchio.ext import commands
import os
import asyncio

CONFIRM_KEYWORD = "CONFIRMAR"  # palabra que debe escribir para confirmar
CONFIRM_TIMEOUT = 30  # segundos hasta que expira la confirmación

class Olvidame(commands.Cog):

    def __init__(self, bot, memoria):
        self.bot = bot
        self.memoria = memoria
        self.confirmando = {}  # usuarios en proceso de confirmación

    @commands.command(name="olvidame")
    async def olvidarme(self, ctx: commands.Context, *args):
        user = ctx.author.name.lower()
        path = self.memoria._user_path(user)

        # Usuario ya en confirmación
        if user in self.confirmando:
            if args and args[0].upper() == CONFIRM_KEYWORD:
                # Borrar datos
                if os.path.exists(path):
                    os.remove(path)
                # Cancelar task de expiración
                self.confirmando[user]["task"].cancel()
                del self.confirmando[user]
                await ctx.send(f"@{user}, tus datos han sido olvidados 😢")
            else:
                await ctx.send(f"@{user}, cancelaste la confirmación. Para confirmar, escribe !olvidame {CONFIRM_KEYWORD}")
            return

        # Primer paso: avisar que se borrará todo
        if os.path.exists(path):
            # Guardamos un task que expirará
            self.confirmando[user] = {"task": asyncio.create_task(self.expirar_confirmacion(ctx, user))}
            await ctx.send(f"@{user}, esto borrará todos tus datos. Para confirmar, escribe !olvidame {CONFIRM_KEYWORD} en los próximos {CONFIRM_TIMEOUT} segundos.")
        else:
            await ctx.send(f"@{user}, no hay nada que olvidar.")

    async def expirar_confirmacion(self, ctx: commands.Context, user: str):
        try:
            await asyncio.sleep(CONFIRM_TIMEOUT)
            if user in self.confirmando:
                # Aviso sarcástico al expirar
                await ctx.send(f"@{user}, ves si es que al final quieres que me acuerde de ti… 😏")
                del self.confirmando[user]
        except asyncio.CancelledError:
            # Si el usuario confirma antes, se cancela la expiración
            pass
