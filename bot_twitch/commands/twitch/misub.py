from twitchio.ext import commands
from datetime import datetime, timezone
from core.memory import Memory
import random


# 🎤 DUEÑO DEL CANAL – sarcasmo infinito
FRASES_DUENO = [
    "no puedes suscribirte a tu propio canal, genio del desastre 🤡",
    "trato VIP infinito: eres el streamer y eso ya es suficiente 😏",
    "ni Jeff Bezos se suscribe a sí mismo… aprende",
    "sub tier ∞ desbloqueado: streamer profesional, deja de llorar",
    "esto es como aplaudirse solo y esperar ovación",
    "el botón existe, pero no para ti… ya eres bastante",
    "sub vitalicia, ego premium, fin de la historia",
    "no necesitas sub, el mundo ya sufre tu existencia",
    "modo autohumillación activado, disfruta",
    "Fantan no llora, pero te observa 🤨"
]

# 🟢 SUB ACTIVO – sarcasmo extremo con halago fingido
FRASES_ES_SUB = [
    "👑 {user}, sigues siendo sub. No te emociones, no todos los días se sobrevive.",
    "😎 {user}, trato premium activo… por ahora, disfruta mientras dure.",
    "🎉 {user}, sigues pagando y Fantan lo nota (y sonríe malvadamente).",
    "😏 {user}, sub confirmado. Eres VIP de la forma más elegante posible.",
    "🟢 {user}, dentro del club… cuidado con el poder, es relativo.",
    "🔥 {user}, sub activo. No preguntes qué pasa aquí, no quieres saberlo.",
    "👀 {user}, VIP detectado. Respira hondo y finge alegría.",
    "✨ {user}, privilegios activos… hasta que Fantan decida lo contrario.",
    "🎟️ {user}, acceso premium vigente. Felicidades… más o menos.",
    "😌 {user}, sigues siendo importante. Al menos para ti."
]

# 🔴 SUB EXPIRADO – humillación máxima
FRASES_SUB_EXPIRADO = [
    "💀 {user}, tu sub ha muerto. Minuto de silencio y lágrimas opcionales.",
    "😬 {user}, fuiste sub… ahora eres recuerdo y nostalgia barata.",
    "🫣 {user}, trato premium caducado. Fantan no llora, tú sí.",
    "⚠️ {user}, la gloria terminó… el botón te mira con desprecio.",
    "😏 {user}, antes eras VIP. Ahora eres espectador mediocre.",
    "👀 {user}, puerta del club cerrada. Golpea, pero no entrarás.",
    "🔥 {user}, el lujo se fue contigo… te quedan cenizas.",
    "🤨 {user}, renovación pendiente. Fantan aprieta los dientes.",
    "⏳ {user}, tiempo agotado. No vuelvas llorando.",
    "😢 {user}, Fantan no te dará tregua. Aprende la lección."
]

# ⚪ NO SUB – incentivo malparido
FRASES_NO_SUB_MISUB = [
    "😏 {user}, no eres sub… aún. Pero oye, prueba suerte, no muerde… casi.",
    "🤨 {user}, sin sub. Mira el club desde fuera, fantasmeando.",
    "😈 {user}, no eres sub… Fantan ríe mientras decides.",
    "🫣 {user}, fuera del club premium. Dentro se mueve el poder… y la rata.",
    "👀 {user}, el botón está ahí. La decepción también. Selecciona sabiamente.",
    "😬 {user}, aún no eres VIP. Te falta aguante.",
    "🎟️ {user}, entrada no incluida. Tal vez algún día… no prometemos.",
    "🤷 {user}, no eres sub. Fantan observa y se burla.",
    "😎 {user}, modo espectador activado. Premium es un mundo cruel.",
    "💸 {user}, sin sub. Fantan recuerda cada pecado."
]


class MiSub(commands.Cog):

    def __init__(self, bot, memoria: Memory):
        self.bot = bot
        self.memoria = memoria

    @commands.command(name="misub")
    async def mi_suscripcion(self, ctx: commands.Context):
        user = ctx.author.name.lower()
        channel = ctx.channel.name.lower()
        user_tag = f"@{user}"

        # 🎤 DUEÑO DEL CANAL – sarcasmo infinito
        if user == channel:
            mensaje = f"{user_tag}, {random.choice(FRASES_DUENO)}"
            await ctx.send(mensaje)
            return

        # 🔍 USUARIO ES SUB
        if user in self.memoria.subs:
            datos_sub = self.memoria.subs[user]
            fecha_raw = datos_sub.get("fecha")

            if isinstance(fecha_raw, str):
                try:
                    fecha_sub = datetime.fromisoformat(fecha_raw)
                except ValueError:
                    fecha_sub = datetime.now(timezone.utc)
            else:
                fecha_sub = datetime.now(timezone.utc)

            ahora = datetime.now(timezone.utc)
            dias_restantes = 30 - (ahora.date() - fecha_sub.date()).days
            dias_restantes = max(dias_restantes, 0)

            # 🔴 SUB EXPIRADO – humillación máxima
            if dias_restantes == 0:
                frase = random.choice(FRASES_SUB_EXPIRADO).format(user=user_tag)
                mensaje = f"{frase} El botón sigue ahí… si te atreves 😏"
            else:
                frase = random.choice(FRASES_ES_SUB).format(user=user_tag)
                mensaje = f"{frase} Te quedan {dias_restantes} días de privilegios, disfrútalos mientras puedas 😈"

        # ⚪ NO SUB – incentivo malparido
        else:
            frase = random.choice(FRASES_NO_SUB_MISUB).format(user=user_tag)
            mensaje = f"{frase} Fantan se ríe mientras decides…"

        await ctx.send(mensaje)

        # 🧠 Guardamos memoria del mensaje
        self.memoria.add_mensaje(user, mensaje)
        self.memoria.guardar_datos()

    