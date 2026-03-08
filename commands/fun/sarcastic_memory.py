from twitchio.ext import commands
import re
import random
from core.memory import Memory
from datetime import datetime, date, timezone
import asyncio

# ---------------- Mensajes sarcásticos cortos ----------------
SARCASTIC_OUTROS = [
    "Y sí, esto queda registrado 😏",
    "Espero que sonrías… aunque sea de nervios 😎",
    "Tu historial resumido, pequeño desastre 🙄",
    "Todo esto es solo para mi diversión 😈",
    "Ahí lo llevas, mini biografía en versión brutal 😏",
]

# ---------------- Introducciones cortas ----------------
NARRATIVE_INTROS = [
    "📖 Hoy echamos un vistazo a @{user}… y sus gloriosos desastres 😏",
    "✨ @{user} otra vez protagonista de situaciones que nadie pidió 🙃",
    "🎬 @{user} y sus hazañas legendarias… o bochornosas 😈",
    "🕵️‍♂️ Una mirada rápida a @{user}, estrella del chat… y de sus propios líos 😎",
    "🏰 @{user}, entre palacios de gloria y fosas de vergüenza 😏",
]

# ---------------- Comentarios tipo zascas cortos ----------------
BOT_COMMENTS = [
    "Ja, esto es demasiado bueno 😏",
    "En serio… ¿alguien hace esto de verdad? 🙄",
    "Nivel ridículo detectado 😈",
    "Prepárense para reír (o llorar) 🤭",
    "¿Pensabas que lo olvidaría? Ja 😎",
]

class SarcasticMemory(commands.Cog):
    def __init__(self, bot, memoria: Memory):
        self.bot = bot
        self.memoria = memoria

    @commands.command(name="soy")
    async def soy(self, ctx: commands.Context, *, contenido: str = None):
        user = ctx.author.name.lower()
        if not contenido:
            await ctx.send(f"@{user}, dime algo que guardar. Ej: !soy un manco")
            return
        contenido = contenido.strip()[:150]
        self.memoria.add_frase(user, contenido)
        await ctx.send(f"🧠 Anotado @{user}: *{contenido}* 😏")

    @commands.command(name="recuerda")
    async def recuerda(self, ctx: commands.Context, *, texto: str = None):
        if not texto:
            await ctx.send("⚡ Cada tropezón cuenta: !recuerda ( <usuario> <acción> en <lugar> ) y voilà, queda guardado en mi papelera virtual… para tu vergüenza eterna 😈")
            return

        autor = ctx.author.name.lower()

        # ---------------- Normalizar texto: quitar acentos y minúsculas ----------------
        import unicodedata
        def normalize(s):
            s = s.lower()
            s = unicodedata.normalize("NFD", s)
            s = "".join(c for c in s if unicodedata.category(c) != "Mn")  # elimina acentos
            return s

        texto_norm = normalize(texto)

        # ---------------- Lista de acciones posibles ----------------
        acciones = [
            "volo", "gano", "perdio", "choco", "salto", "corrio", "rompio",
            "grito", "lloro", "fallo", "aplasto", "esquivo", "ataco", "defendio",
            "piloto", "condujo", "abandono", "celebro", "insulto", "ignoro"
            # puedes añadir más aquí
        ]

        acciones_regex = "|".join(acciones)
        pattern = fr"(\w+)\s+({acciones_regex})\s*(?:en\s+(.+))?"

        match = re.match(pattern, texto_norm)
        if match:
            sujeto, accion, lugar = match.groups()
            self.memoria.add_hecho(
                sujeto=sujeto,
                accion=accion,
                lugar=lugar if lugar else None,
                autor=autor
            )
            await ctx.send(f"🧠 Anotado: {sujeto} {accion}" + (f" en {lugar}" if lugar else "") + " 😏")
        else:
            self.memoria.add_recuerdo(autor, texto)
            await ctx.send(f"🧠 Guardado @{autor}: *{texto}* 😈")
            
            
    # ---------------- Comando que acepta usuario ----------------
    @commands.command(name="quiensoy")
    async def quiensoy(self, ctx: commands.Context, usuario: str = None):
        target_user = usuario.lower() if usuario else ctx.author.name.lower()
        await self._mini_relato_humano(ctx, target_user)

    @commands.command(name="quesabesde")
    async def quesabes(self, ctx: commands.Context, usuario: str = None):
        target_user = usuario.lower() if usuario else ctx.author.name.lower()
        await self._mini_relato_humano(ctx, target_user)

    # ---------------- Mini relato sarcástico estilo humano ----------------
    async def _mini_relato_humano(self, ctx, user):
        self.memoria.ensure_user(user)
        data = self.memoria._load_user(user)

        frases = data.get("perfil", {}).get("soy", [])
        recuerdos_dict = data.get("recuerdos", {}).get("mensaje", {})
        hechos_list = self.memoria.buscar_hechos(user)

        if not frases and not recuerdos_dict and not hechos_list:
            await ctx.send(f"@{ctx.author.name}, no sé nada de {user}… por ahora 😏")
            return

        relato = []

        # --- Intro ---
        relato.append(random.choice(NARRATIVE_INTROS).format(user=user))

        # --- Frase de perfil relevante ---
        if frases:
            perfil_frase = random.choice(frases)
            relato.append(f"Por cierto, {user} dijo: «{perfil_frase}»… {random.choice(BOT_COMMENTS)}")

        # --- Recuerdos recientes (1–2) ---
        if recuerdos_dict:
            ultimos = sorted(recuerdos_dict.items(), key=lambda x: x[1]["ultima_vez"], reverse=True)
            seleccionados = random.sample(ultimos, min(2, len(ultimos)))
            recuerdos_texto = ", ".join(f"«{rec}»" for rec, _ in seleccionados)
            relato.append(f"Recientemente comentó: {recuerdos_texto}… {random.choice(BOT_COMMENTS)}")

        # --- Hechos aleatorios (1–2) ---
        if hechos_list:
            seleccionados = random.sample(hechos_list, min(2, len(hechos_list)))
            hechos_texto = ", ".join(f"{h['accion']} en {h['lugar']}" for h in seleccionados)
            relato.append(f"En su historial: {hechos_texto}… {random.choice(BOT_COMMENTS)}")

        # --- Outro ---
        relato.append(random.choice(SARCASTIC_OUTROS))

        # --- Construir mensaje final ---
        mensaje_final = " | ".join(relato)
        mensaje_final = mensaje_final[:350]

        await ctx.send(f"@{ctx.author.name} {mensaje_final}")

