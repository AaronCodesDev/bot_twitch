import math
from twitchio.ext import commands
# IMPORTANTE: Asegúrate de que la ruta de importación coincida con tu estructura
from core.persistence import es_canal_pro 

class Carrera(commands.Cog):
    def __init__(self, bot, memoria):
        self.bot = bot
        self.memoria = memoria

    @commands.command(name="carrera")
    async def carrera(self, ctx: commands.Context):
        # --- NUEVO CHEQUEO DE SUSCRIPCIÓN ---
        # Verificamos si el canal donde se ejecuta el comando tiene nivel PRO
        if not es_canal_pro(ctx.channel.name):
            await ctx.send(f"⚠️ @{ctx.author.name}, el módulo de iRacing es exclusivo para la versión PRO del bot.")
            return

        # --- TU LÓGICA ORIGINAL (SIN CAMBIOS) ---
        listener = getattr(self.bot, "iracing_listener", None)

        if not listener or not listener.ir.is_initialized:
            await ctx.send("❌ iRacing no detectado. El simulador debe estar abierto y en sesión.")
            return

        ir = listener.ir

        try:
            # --- Información del Piloto y Coche ---
            driver_idx = ir["DriverInfo"]["DriverCarIdx"]
            driver_data = ir["DriverInfo"]["Drivers"][driver_idx]

            piloto = driver_data["UserName"]
            car_number = driver_data["CarNumber"]
            car_name = driver_data["CarScreenName"]

            # --- Circuito ---
            circuito = ir["WeekendInfo"]["TrackDisplayName"]

            # --- Cálculo de SOF y Total de Coches ---
            drivers_list = ir["DriverInfo"]["Drivers"]
            iratings = []

            for d in drivers_list:
                if d["IRating"] > 0 and not d["IsSpectator"]:
                    iratings.append(d["IRating"])

            total_coches = len(iratings)
            sof = int(sum(iratings) / total_coches) if total_coches > 0 else 0

            # --- Posición para ganar iRating (estimación) ---
            pos_ganar = math.ceil(total_coches / 2)

            # --- Posición Actual segura ---
            is_on_track = driver_data.get("IsOnTrack", False) or driver_data.get("CarIdxOnTrack", 0) > 0

            if driver_data["IsSpectator"] or not is_on_track:
                pos_actual_text = "No ha salido aún"
            else:
                pos_actual = driver_data.get("CarClassPosition", ir.get("PlayerCarClassPosition", 0)) + 1
                pos_actual_text = f"P{pos_actual}"

            # --- Construcción del mensaje ---
            mensaje = (
                f"🏎️ {piloto} con el {car_name} [#{car_number}] está corriendo en {circuito}. "
                f"La sala tiene un SOF de {sof} con un total de {total_coches} coches. "
                f"Actualmente va {pos_actual_text} y para ganar iRating tendría que quedar P{pos_ganar} o mejor. 🏁"
            )

            await ctx.send(mensaje)

        except Exception as e:
            print(f"Error en !carrera: {e}")
            await ctx.send("No puedo leer los datos de la telemetría. ¿Estás en el muro? 🧱")