from twitchio.ext import commands

class Pos(commands.Cog):

    def __init__(self, bot, memoria):
        self.bot = bot
        self.memoria = memoria

    @commands.command(name="pos")
    async def pos(self, ctx: commands.Context):
        """
        Muestra la posición actual del piloto en tiempo real.
        """
        listener = getattr(self.bot, "iracing_listener", None)

        if not listener or not listener.ir.is_initialized:
            await ctx.send("🏎️ iRacing no está conectado… posición desconocida.")
            return

        ir = listener.ir

        try:
            # 1. Nombre del piloto (bloque DriverInfo estático)
            driver_idx = ir["DriverInfo"]["DriverCarIdx"]
            drivers = ir["DriverInfo"]["Drivers"]
            piloto = drivers[driver_idx]["UserName"]

            # 2. Posición REAL (Variables de telemetría en vivo)
            # Usamos PlayerCarClassPosition para la posición en su clase (útil en multicapa)
            # Si prefieres posición global, usa PlayerCarPosition
            posicion_real = ir["PlayerCarClassPosition"] 
            
            # 3. Total de pilotos (contamos los que tienen iRating activo en la sesión)
            total_pilotos = len([d for d in drivers if d["IRating"] > 0])

            # 4. Validar que la posición sea lógica
            if posicion_real > 0:
                await ctx.send(f"📍 {piloto} está en P{posicion_real} de {total_pilotos} pilotos.")
            else:
                await ctx.send(f"🏁 {piloto}, la sesión aún no ha comenzado o no estás en pista.")

        except Exception as e:
            print(f"Error en comando POS: {e}")
            await ctx.send("⚠️ No pude leer la posición actual. Inténtalo de nuevo en un momento.")