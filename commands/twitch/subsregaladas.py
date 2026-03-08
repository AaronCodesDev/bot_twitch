from twitchio.ext import commands
from datetime import datetime
from collections import Counter
import json
import os

DATA_FOLDER = 'data'
SUBS_MES_FILE = os.path.join(DATA_FOLDER, 'subs')


class SubsRegaladas(commands.Cog):

    def __init__(self, bot, memoria):
        self.bot = bot
        self.memoria = memoria

    @commands.command(name='subsregaladas')
    async def subs_regaladas(self, ctx):
        if not (ctx.author.is_mod or ctx.author.is_broadcaster):
            await ctx.send('❌ No tienes permiso para ver las subs regaladas.')
            return

        mes = datetime.now().strftime("%Y-%m")
        archivo = os.path.join(SUBS_MES_FILE, f'subs_{mes}.json')

        if not os.path.exists(archivo):
            await ctx.send('❌ Este mes nadie ha regalado nada (sospechoso) 🤨')
            return

        try:
            with open(archivo, 'r', encoding='utf-8') as f:
                datos = json.load(f)
        except json.JSONDecodeError:
            await ctx.send('⚠️ Error leyendo los datos de subs. El JSON está corrupto.')
            return

        regaladas = datos.get('regaladas', [])
        if not regaladas:
            await ctx.send('📭 Sin subs regaladas este mes.')
            return

        # Sumar las cantidades por regalador considerando ambos formatos
        contador_regalos = {}
        detalle_list = []

        for r in regaladas:
            if 'regalador' in r and 'receptor' in r:  # Formato antiguo
                regalador = r['regalador']
                receptor = r['receptor']
                cantidad = r.get('cantidad', 1)
            elif 'from' in r and 'to' in r:  # Formato nuevo
                regalador = r['from']
                receptor = r['to']
                cantidad = r.get('cantidad', 1)
            else:
                continue  # Ignorar entradas que no tengan datos válidos

            # Acumular cantidad por regalador
            contador_regalos[regalador] = contador_regalos.get(regalador, 0) + cantidad
            detalle_list.append(f"@{regalador} regaló {cantidad} sub{'s' if cantidad>1 else ''} a @{receptor}")

        if not contador_regalos:
            await ctx.send('Resumen de subs regaladas este mes: Ninguna sub registrada correctamente. Detalle: Ningún detalle disponible.')
            return

        # Crear resumen
        resumen = '\n'.join(
            f"- @{usuario} : {cantidad} sub{'s' if cantidad > 1 else ''}"
            for usuario, cantidad in contador_regalos.items()
        )

        # Crear detalle
        detalle = ' | '.join(detalle_list)

        mensaje = f"📊 Resumen de subs regaladas este mes:\n{resumen}\n\n📜 Detalle:\n{detalle}"
        await ctx.send(mensaje)
