from twitchio.ext import commands
import asyncio
import random

SEARCH_PHRASES = [
    "🔎 Buscando al piloto…",
    "⌛ Ajustando las gafas de realidad virtual…",
    "🛰️ Escaneando la parrilla…",
    "💨 El viento susurra el SOF… casi listo",
    "🤔 Calculando split y SOF… paciencia",
    "🚦 Encendiendo semáforos… casi listo",
]

class SOF(commands.Cog):

    def __init__(self, bot, memoria):
        self.bot = bot
        self.memoria = memoria

    @commands.command(name="sof")
    async def sof(self, ctx: commands.Context):
        listener = getattr(self.bot, "iracing_listener", None)
        
        if not listener or not listener.ir.is_initialized:
            await ctx.send("🏎️ iRacing no está activo… SOF desconocido.")
            return

        ir = listener.ir
        
        # Enviamos frase de espera
        await ctx.send(random.choice(SEARCH_PHRASES))
        await asyncio.sleep(1)

        try:
            # 1. Obtener información base
            drivers = ir["DriverInfo"]["Drivers"]
            driver_idx = ir["DriverInfo"]["DriverCarIdx"]
            
            if not drivers or driver_idx is None:
                await ctx.send("🤖 No puedo encontrar datos de los pilotos.")
                return

            piloto = drivers[driver_idx]["UserName"]
            # Intentamos sacar el split si el listener lo tiene, si no, "Desconocido"
            split = "Desconocido"
            if hasattr(listener, "get_player_split"):
                split = listener.get_player_split() or "Desconocido"

            # 2. CALCULAR EL SOF (PRIMERO CREAMOS LA LISTA)
            iratings = [d["IRating"] for d in drivers if d["IRating"] > 0]
            num_pilotos = len(iratings) # AHORA SÍ, después de crearla

            if num_pilotos > 0:
                sof_value = sum(iratings) // num_pilotos
                
                if sof_value <= 1:
                    await self.enviar_frase_graciosa(ctx, piloto, split)
                else:
                    # Mensaje final con SOF y número de pilotos
                    await ctx.send(f"💪 {piloto} → SOF {sof_value} | {num_pilotos} Pilotos en pista")
            else:
                await self.enviar_frase_graciosa(ctx, piloto, split)

        except Exception as e:
            # Esto te ayudará a ver errores en la consola si algo falla
            print(f"Error en comando SOF: {e}")
            await ctx.send("⚠️ Error al procesar los datos de telemetría.")

    async def enviar_frase_graciosa(self, ctx, piloto, split):
        frases_graciosas = [
            f"El piloto {piloto}, el SOF está de vacaciones… 😅",
            f"💨 El piloto {piloto} → SOF secreto, shhh…",
            f"🤔 El piloto {piloto}, hoy el SOF es un misterio…",
            f"🏎️ El piloto {piloto} → SOF en modo ninja.",
        ]
        await ctx.send(random.choice(frases_graciosas))