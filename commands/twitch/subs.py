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

# Frases especiales últimos días (1–6)
ULTIMOS_DIAS = {
    6: [
        "⏳ {user}, quedan 6 días… el reloj corre.",
        "😬 {user}, empieza la última semana.",
        "🔥 {user}, 6 días para salvar la sub.",
        "⚠️ {user}, cuenta atrás activada.",
        "😏 {user}, aún hay esperanza."
    ],
    5: [
        "⏰ {user}, solo 5 días…",
        "😱 {user}, el pánico empieza.",
        "💀 {user}, el desastre se acerca.",
        "😈 {user}, el rojo te observa.",
        "⚡ {user}, decide ya."
    ],
    4: [
        "⚠️ {user}, 4 días restantes.",
        "🔥 {user}, la cuenta atrás sigue.",
        "😅 {user}, todavía puedes salvarte.",
        "😎 {user}, no todo está perdido.",
        "😏 {user}, corre."
    ],
    3: [
        "🔥 {user}, solo 3 días…",
        "💀 {user}, el drama es real.",
        "⏳ {user}, el tiempo se agota.",
        "⚡ {user}, último aviso.",
        "😬 {user}, actúa ya."
    ],
    2: [
        "💀 {user}, 2 días…",
        "😱 {user}, pánico máximo.",
        "⚠️ {user}, casi no hay tiempo.",
        "🔥 {user}, corre o cae.",
        "😈 {user}, tensión al límite."
    ],
    1: [
        "😱 {user}, último día…",
        "💀 {user}, hoy se decide todo.",
        "⚡ {user}, o renuevas o mueres.",
        "🔥 {user}, el final está aquí.",
        "😬 {user}, últimas 24h."
    ]
}

FRASES_NO_SUB = [
    "😏 {user} no es sub… pero oye, justo hoy es un gran día para no ganar nada. O sí. Quién sabe.",
    "🤨 {user} sin sub. Los sorteos existen, la suerte también… Fantan ya es otro tema.",
    "😈 {user} no es sub todavía. Igual hoy cae premio. Igual Fantan se hace el loco.",
    "😂 {user} no es sub… pero tranquilo, los premios no muerden. Fantan un poco.",
    "😎 {user} fuera del club de subs. Dentro hay sorteos, risas… y promesas vagas.",
    "🫣 {user} aún no es sub. Los subs suelen ganar más… suele. A veces. Quizá.",
    "👀 {user} no es sub. El botón está ahí, el sorteo también, la decisión es tuya.",
    "🤷 {user} sin sub. Igual hoy no pasa nada. Igual pasa algo. Fantan decide.",
    "😬 {user} no es sub todavía. Dicen que los subs tienen más suerte… dicen.",
    "💸 {user} no es sub. Fantan no promete premios, pero le gusta que la gente pruebe."
]

# ───────── COG ─────────

class MostrarSubs(commands.Cog):
    def __init__(self, bot, memoria):
        self.bot = bot
        self.memoria = memoria

    # ───── Helpers (NO TOCAN Memory) ─────

    def _get_inicio_sub(self, user: str):
        data = self.memoria.subs.get(user)
        if not data or not isinstance(data, dict):
            return None

        fecha = data.get("fecha")
        if not fecha:
            return None

        try:
            dt = datetime.fromisoformat(fecha)
            if dt.tzinfo is None:
                dt = dt.replace(tzinfo=timezone.utc)    
            return dt
        except Exception:
            return None

    def _dias_restantes_sub(self, user: str) -> int:
        inicio = self._get_inicio_sub(user)
        if not inicio:
            return -1

        fin = inicio + timedelta(days=SUB_DURACION_DIAS)
        return (fin - datetime.now(timezone.utc)).days

    def _dias_como_sub(self, user: str) -> int:
        inicio = self._get_inicio_sub(user)
        if not inicio:
            return 0
        delta = datetime.now(timezone.utc) - inicio
        return max(0, (datetime.now(timezone.utc) - inicio).days)

    def _is_sub(self, user: str) -> bool:
        return self._dias_restantes_sub(user) >= 0

    def _obtener_frase_color_tag(self, restantes, user):
        if restantes < 0:
            return None, None, None

        user_tag = f"@{user}"

        if 1 <= restantes <= 6:
            frase = random.choice(ULTIMOS_DIAS[restantes]).format(user=user_tag)
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

    # ───── Comando !subs ─────

    @commands.command(name="subs")
    async def mostrar_subs(self, ctx: commands.Context, usuario: str = None):
        es_mod = ctx.author.is_mod or ctx.author.is_broadcaster

        # Consulta individual
        if usuario:
            usuario = usuario.lstrip("@").lower()

            if usuario == CUENTA_PROPIA:
                return

            if not self._is_sub(usuario):
                frase = random.choice(FRASES_NO_SUB).format(user=f"@{usuario}")
                return await ctx.send(frase)

            restantes = self._dias_restantes_sub(usuario)
            dias_totales = self._dias_como_sub(usuario)

            frase, color, tag = self._obtener_frase_color_tag(restantes, usuario)

            if frase:
                await ctx.send(
                    f"{color} @{usuario} es sub hace {dias_totales} días ({tag}). {frase}"
                )
            return

        # Lista completa (mods)
        if not es_mod:
            return await ctx.send("❌ Solo mods pueden usar !subs sin nombre.")

        subs_activos = [
            u for u in self.memoria.subs
            if u != CUENTA_PROPIA and self._dias_restantes_sub(u) >= 0
        ]

        if not subs_activos:
            return await ctx.send("📄 No hay subs activos 😢")

        subs_activos.sort(key=lambda u: self._dias_restantes_sub(u))

        mensajes = []
        for user in subs_activos:
            restantes = self._dias_restantes_sub(user)
            frase, color, tag = self._obtener_frase_color_tag(restantes, user)
            mensajes.append(f"{color} ({tag}) — {frase}")

        await ctx.send("⭐ Subs activos del mes:\n" + "\n".join(mensajes))
