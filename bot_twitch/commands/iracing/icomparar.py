import math
import random
import re
import traceback
from twitchio.ext import commands
from phrases.iracing.icomparar import (
    frase_posicion_aleatoria,
    frase_lastlap,
    frase_irating_brutal
)

class IComparar(commands.Cog):
    def __init__(self, bot, memoria):
        self.bot = bot
        self.memoria = memoria

    @commands.command(name="icomparar")
    async def icomparar(self, ctx: commands.Context, *, nombre_piloto: str):

        listener = getattr(self.bot, "iracing_listener", None)
        if not listener or not listener.ir.is_initialized:
            await ctx.send("❌ iRacing no detectado. El simulador debe estar abierto.")
            return

        ir = listener.ir

        try:
            print(f"\n--- [DEBUG !icomparar] Inicio ---")
            drivers_list = ir["DriverInfo"]["Drivers"]

            def normalizar(txt):
                return re.sub(r"\s+", " ", str(txt).lower().strip())

            nombre_busqueda = normalizar(nombre_piloto)

            # 1. DATOS TUYOS
            tu_idx = ir["DriverInfo"]["DriverCarIdx"]
            tu_data = next((d for d in drivers_list if d["CarIdx"] == tu_idx), None)
            
            if not tu_data:
                print("DEBUG ERROR: No se encontró tu CarIdx")
                return

            tu_nombre = tu_data.get("UserName", "Piloto Local")
            tu_irating = tu_data.get("IRating", 0)
            tu_lastlap = ir["CarIdxLastLapTime"][tu_idx]

            # 2. BUSCAR AL RIVAL
            otro_data = None
            for d in drivers_list:
                n_driver = normalizar(d.get("UserName", ""))
                c_num = str(d.get("CarNumber", "")).lower()
                if nombre_busqueda == n_driver or nombre_busqueda in n_driver or nombre_busqueda == c_num:
                    otro_data = d
                    break
            
            if not otro_data:
                print(f"DEBUG: Rival '{nombre_piloto}' no encontrado.")
                await ctx.send(f"❌ No encontré al piloto '{nombre_piloto}'.")
                return

            # 3. DATOS DEL RIVAL
            otro_nombre = otro_data.get("UserName", "Rival")
            otro_idx = otro_data.get("CarIdx")
            otro_irating = otro_data.get("IRating", 0)
            otro_lastlap = ir["CarIdxLastLapTime"][otro_idx]

            print(f"DEBUG: {tu_nombre}({tu_irating}) vs {otro_nombre}({otro_irating})")

            # 4. LÓGICA DE COMPARACIÓN DE IRATING (SIN POSICIONES)
            dif_ir = tu_irating - otro_irating # Diferencia a tu favor o en contra
            
            if dif_ir <= -1000:
                comentario = f"💀 **¡NIVEL ALIEN!** {otro_nombre} te saca {abs(dif_ir)} puntos. Es un suicidio intentar seguirle... 🙏"
            elif dif_ir <= -500:
                comentario = f"😰 **Peligro:** {otro_nombre} es bastante más pro que tú (+{abs(dif_ir)} iR). ¡Toca sufrir!"
            elif dif_ir < 0:
                comentario = f"📉 **Favorito el rival:** {otro_nombre} tiene {abs(dif_ir)} puntos más. Está un peldaño por encima."
            elif dif_ir > 500:
                comentario = f"😎 **Superioridad clara:** Tienes +{dif_ir} de iRating. Deberías merendarte a {otro_nombre} fácil."
            elif dif_ir > 0:
                comentario = f"📈 **Vas por delante:** Tienes {dif_ir} puntos más de iR. ¡Demuestra que te los has ganado!"
            else:
                comentario = f"⚔️ **Igualdad máxima:** Tenéis el mismo iRating. ¡Aquí mandan las manos!"

            # 5. TIEMPOS DE VUELTA
            if tu_lastlap > 0 and otro_lastlap > 0:
                # Usamos la frase importada de ritmo
                ritmo = frase_lastlap(tu_nombre, tu_lastlap, otro_nombre, otro_lastlap)
            else:
                ritmo = "⏱️ Aún no hay vueltas limpias para comparar ritmos."

            # 6. MENSAJE FINAL (LIMPIO Y SIN POSICIONES)
            circuito = ir["WeekendInfo"]["TrackDisplayName"]
            
            mensaje = (
                f"🏎️ **Comparativa en {circuito}:**\n"
                f"📊 {tu_nombre} ({tu_irating} iR) vs {otro_nombre} ({otro_irating} iR)\n"
                f"{comentario}\n"
                f"{ritmo}"
            )

            print("DEBUG: Mensaje generado correctamente.")
            await ctx.send(mensaje)

        except Exception as e:
            print("--- ERROR EN !ICOMPARAR ---")
            traceback.print_exc()
            await ctx.send("🔥 Error leyendo la telemetría.")