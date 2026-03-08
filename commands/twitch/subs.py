from twitchio.ext import commands
import random
from datetime import datetime, timezone, timedelta

CUENTA_PROPIA = "fantan"
SUB_DURACION_DIAS = 30

# ───────── FRASES ─────────
FRASES_SUBS = {
    "rojo": [
        "😱 {user}, última semana… ¡corre que se te acaba la sub!",
        "🔥 {user} está en rojo total… ¿renovamos o lloramos?",
        "⚠️ {user}, te queda nada… aún puedes volver a verde 👀",
        "😬 {user} en rojo… el drama está servido.",
        "💀 {user}, el rojo no perdona. Últimos días.",
        "😈 {user}, ¿te atreves a jugar con el tiempo?",
        "😩 {user}, el pánico rojo ya se nota.",
        "😳 {user}, el contador corre más rápido de lo que crees.",
        "🔥 {user} al borde del desastre…",
        "⚠️ {user}, decide tu destino ahora."
    ],
    "naranja": [
        "🟠 {user}, segunda semana… el pánico empieza 😏",
        "😉 {user}, no te confíes, el rojo acecha.",
        "😎 {user} está naranja elegante.",
        "🫣 {user}, aún no es rojo… todavía.",
        "😏 {user}, naranja suave pero peligroso.",
        "😬 {user}, mitad de camino, mitad de drama.",
        "😅 {user}, dos semanas y contando.",
        "😐 {user}, el rojo se acerca sigilosamente.",
        "😳 {user}, alerta naranja activada.",
        "🤨 {user}, todavía puedes salvarte."
    ],
    "amarillo": [
        "🟡 {user}, a mitad de camino… disfruta 😏",
        "🙂 {user}, amarillo tranquilo por ahora.",
        "😅 {user}, medio mes, medio estrés.",
        "😌 {user}, amarillo seguro.",
        "😎 {user}, los rojos te envidian.",
        "😉 {user}, aún puedes respirar.",
        "😏 {user}, todo bajo control… de momento.",
        "😬 {user}, ojo que la naranja ya se ve.",
        "🤔 {user}, planifica antes del rojo.",
        "😌 {user}, disfruta mientras dure."
    ],
    "verde": [
        "🟢 {user}, fresco total 😎",
        "😎 {user} está verde brillante.",
        "🎉 {user}, sub top del mes.",
        "😁 {user}, el paraíso del sub.",
        "😌 {user}, la vida es buena aquí arriba.",
        "😏 {user}, rey del mes.",
        "😉 {user}, disfruta la calma.",
        "🎊 {user}, verde glorioso.",
        "😄 {user}, mes asegurado.",
        "🟢 {user}, tranquilidad absoluta."
    ]
}

ULTIMOS_DIAS = {
    6: ["⏳ {user}, quedan 6 días… el reloj corre.", "😬 {user}, empieza la última semana.", "🔥 {user}, 6 días para salvar la sub."],
    5: ["⏰ {user}, solo 5 días…", "😱 {user}, el pánico empieza.", "💀 {user}, el desastre se acerca."],
    4: ["⚠️ {user}, 4 días restantes.", "🔥 {user}, la cuenta atrás sigue.", "😅 {user}, todavía puedes salvarte."],
    3: ["🔥 {user}, solo 3 días…", "💀 {user}, el drama es real.", "⏳ {user}, el tiempo se agota."],
    2: ["💀 {user}, 2 días…", "😱 {user}, pánico máximo.", "⚠️ {user}, casi no hay tiempo."],
    1: ["😱 {user}, último día…", "💀 {user}, hoy se decide todo.", "⚡ {user}, o renuevas o mueres."]
}

FRASES_NO_SUB = [
    "😏 {user} no es sub… pero oye, justo hoy es un gran día para no ganar nada.",
    "🤨 {user} sin sub. Los sorteos existen, la suerte también… Fantan ya es otro tema.",
    "😈 {user} no es sub todavía. Igual hoy cae premio.",
    "😂 {user} no es sub… pero tranquilo, los premios no muerden. Fantan un poco."
]

# ───────── COG ─────────

class MostrarSubs(commands.Cog):
    def __init__(self, bot, memoria):
        self.bot = bot
        self.memoria = memoria

    def _get_inicio_sub(self, user: str):
        # Buscamos en los suscriptores cargados por el bot
        data = self.bot.suscriptores.get(user.lower())
        if not data or not isinstance(data, dict):
            return None

        fecha = data.get("fecha")
        if not fecha:
            return None

        try:
            # Limpiamos el formato de fecha para que Python lo entienda
            dt = datetime.fromisoformat(fecha.replace("Z", "+00:00"))
            if dt.tzinfo is None:
                dt = dt.replace(tzinfo=timezone.utc)    
            return dt
        except Exception:
            return None

    def _dias_restantes_sub(self, user: str) -> int:
        inicio = self._get_inicio_sub(user)
        if not inicio:
            return -1
        
        ahora = datetime.now(timezone.utc)
        # Calculamos cuánto tiempo ha pasado
        dias_desde_inicio = (ahora - inicio).days
        
        # Como Twitch funciona por ciclos de 30 días, calculamos
        # cuánto le queda para terminar su "mes" actual de sub.
        dias_consumidos_este_mes = dias_desde_inicio % 30
        restantes = 30 - dias_consumidos_este_mes
        return restantes

    def _dias_como_sub(self, user: str) -> int:
        inicio = self._get_inicio_sub(user)
        if not inicio:
            return 0
        return max(0, (datetime.now(timezone.utc) - inicio).days)

    def _is_sub(self, user: str) -> bool:
        # Es sub si está en nuestra lista de memoria
        return user.lower() in self.bot.suscriptores

    def _obtener_frase_color_tag(self, restantes, user):
        user_tag = f"@{user}"
        
        # Lógica de colores y frases aleatorias
        if 1 <= restantes <= 6:
            frase = random.choice(ULTIMOS_DIAS.get(restantes, ["⏳ {user}, queda poco..."])).format(user=user_tag)
            return frase, "🔴", f"{restantes} días"
        
        if restantes <= 7:
            frase = random.choice(FRASES_SUBS["rojo"]).format(user=user_tag)
            return frase, "🔴", f"{restantes} días"
        
        if restantes <= 15:
            frase = random.choice(FRASES_SUBS["naranja"]).format(user=user_tag)
            return frase, "🟠", f"{restantes} días"
        
        if restantes <= 22:
            frase = random.choice(FRASES_SUBS["amarillo"]).format(user=user_tag)
            return frase, "🟡", f"{restantes} días"
        
        frase = random.choice(FRASES_SUBS["verde"]).format(user=user_tag)
        return frase, "🟢", f"{restantes} días"

    @commands.command(name="subs")
    async def mostrar_subs(self, ctx: commands.Context, usuario: str = None):
        es_mod = ctx.author.is_mod or ctx.author.is_broadcaster

        # 1. Consulta individual (!subs @usuario)
        if usuario:
            usuario = usuario.lstrip("@").lower()
            
            # BLOQUEO 1: Si el usuario consultado eres tú, el bot no responde
            if usuario == CUENTA_PROPIA:
                return

            if not self._is_sub(usuario):
                return await ctx.send(random.choice(FRASES_NO_SUB).format(user=f"@{usuario}"))

            restantes = self._dias_restantes_sub(usuario)
            dias_totales = self._dias_como_sub(usuario)
            frase, color, tag = self._obtener_frase_color_tag(restantes, usuario)

            if frase:
                await ctx.send(f"{color} @{usuario} es sub hace {dias_totales} días ({tag}). {frase}")
            return

        # 2. Lista completa para Mods/Broadcaster (!subs)
        if not es_mod:
            return await ctx.send("❌ Solo mods pueden ver la lista completa.")

        # BLOQUEO 2: Filtramos la lista para que NO te incluya a ti
        subs_activos = [
            u for u in self.bot.suscriptores.keys() 
            if u.lower() != CUENTA_PROPIA
        ]

        if not subs_activos:
            return await ctx.send("📄 No hay subs activos en la base de datos 😢")

        # Ordenamos por los que están más cerca de caducar (rojos primero)
        subs_activos.sort(key=lambda u: self._dias_restantes_sub(u))

        # Construimos el mensaje con frases para cada uno
        mensajes = []
        # Mostramos los primeros 5 subs reales
        for user in subs_activos[:5]: 
            restantes = self._dias_restantes_sub(user)
            frase, color, tag = self._obtener_frase_color_tag(restantes, user)
            mensajes.append(f"{color} ({tag}) — {frase}")

        total = len(subs_activos)
        await ctx.send(f"⭐ {total} Subs activos del mes:\n" + " | ".join(mensajes))