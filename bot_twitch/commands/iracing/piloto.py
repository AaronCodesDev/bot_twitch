from twitchio.ext import commands

class Piloto(commands.Cog):

    def __init__(self, bot, memoria):
        self.bot = bot
        self.memoria = memoria

    @commands.command(name="piloto")
    async def piloto(self, ctx: commands.Context):
        """
        Muestra el iRating y SR del piloto actual, con separador de miles en iRating.
        """

        listener = getattr(self.bot, "iracing_listener", None)

        if not listener or not listener.ir.is_initialized:
            await ctx.send(
                "Tu piloto ahora mismo no está en pista… estará farmeando SR en time trial."
            )
            return

        ir = listener.ir

        # ───────── Nombre del piloto ─────────
        try:
            driver_idx = ir["DriverInfo"]["DriverCarIdx"]
            piloto = ir["DriverInfo"]["Drivers"][driver_idx]["UserName"]
        except Exception:
            piloto = "Tu piloto"

        # ───────── iRating y SR ─────────
        irating = listener.get_player_irating()
        sr = listener.get_player_sr()

        # ───────── Formatear iRating con punto ─────────
        if irating is not None:
            irating_formatted = f"{irating:,}".replace(",", ".")  # 1234 -> 1.234
            await ctx.send(
                f"🏁 {piloto} → {irating_formatted} iR | {sr} SR | top split en su mente."
            )
        else:
            await ctx.send("No encuentro el iRating… has roto hasta el SDK.")