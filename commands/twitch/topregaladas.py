from twitchio.ext import commands
from datetime import datetime
from collections import Counter
import json
import os

DATA_FOLDER = 'data'
SUBS_MES_FILE = os.path.join(DATA_FOLDER, 'subs')


class TopRegaladas(commands.Cog):

    def __init__(self, bot, memoria):
        self.bot = bot
        self.memoria = memoria
        
    @commands.command(name="topregaladas")
    async def top_regaladas(self, ctx):
        mes = datetime.now().strftime("%Y-%m")
        archivo = os.path.join(SUBS_MES_FILE, f'subs_{mes}.json')

        if not os.path.exists(archivo):
            await ctx.send('❌ Este mes nadie ha regalado subs (sospechoso) 🤨')
            return

        try:
            with open(archivo, 'r', encoding='utf-8') as f:
                datos = json.load(f)
        except json.JSONDecodeError:
            await ctx.send('⚠️ Error leyendo los datos de subs. El JSON está corrupto.')
            return

        regaladas = datos.get('regaladas', [])
        if not regaladas:
            await ctx.send('📭 Sin subs regaladas este mes. El capitalismo está fallando.')
            return

        # Contar subs por regalador, considerando ambos formatos y sumando cantidad
        contador = {}
        for r in regaladas:
            if 'regalador' in r and 'receptor' in r:  # formato antiguo
                regalador = r['regalador']
                cantidad = r.get('cantidad', 1)
            elif 'from' in r and 'to' in r:  # formato nuevo
                regalador = r['from']
                cantidad = r.get('cantidad', 1)
            else:
                continue  # ignorar entradas inválidas

            contador[regalador] = contador.get(regalador, 0) + cantidad

        if not contador:
            await ctx.send('📭 Ningún regalador registrado correctamente este mes.')
            return

        total_regaladores = len(contador)
        mensajes = []

        for i, (u, c) in enumerate(sorted(contador.items(), key=lambda x: x[1], reverse=True), 1):
            usuario_mencion = f"@{u}"
            if c == 1:
                msg = f"{i}. {usuario_mencion} : {c} sub… valiente, pero podrías esforzarte un poquito más 😅"
            elif c == 2:
                msg = f"{i}. {usuario_mencion} : {c} subs, repartiendo cariño moderadamente 😏"
            elif 3 <= c <= 5:
                msg = f"{i}. {usuario_mencion} : {c} subs, casi Santa Claus 🎅, pero aún te falta"
            elif 6 <= c <= 10:
                msg = f"{i}. {usuario_mencion} : {c} subs, héroe del mes 🦸‍♂️🔥 ¡que se corra la voz!"
            else:
                msg = f"{i}. {usuario_mencion} : {c} subs, leyenda viva ⚡💥, ya deberías tener estatua"
            mensajes.append(msg)

        mensaje_final = f"🏆 Top regaladores de subs este mes ({total_regaladores} en total):\n" + "\n".join(mensajes)
        await ctx.send(mensaje_final)
