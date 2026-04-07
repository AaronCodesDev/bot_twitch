# commands/fun/sarcastic_memory.py
from twitchio.ext import commands
from core.database import db
import re
import random
from datetime import datetime
import asyncio
import unicodedata

SARCASTIC_OUTROS = [
    "Y sí, esto queda registrado 😏",
    "Espero que sonrías… aunque sea de nervios 😎",
    "Tu historial resumido, pequeño desastre 🙄",
    "Todo esto es solo para mi diversión 😈",
    "Ahí lo llevas, mini biografía en versión brutal 😏",
]

NARRATIVE_INTROS = [
    "📖 Hoy echamos un vistazo a @{user}… y sus gloriosos desastres 😏",
    "✨ @{user} otra vez protagonista de situaciones que nadie pidió 🙃",
    "🎬 @{user} y sus hazañas legendarias… o bochornosas 😈",
    "🕵️‍♂️ Una mirada rápida a @{user}, estrella del chat… y de sus propios líos 😎",
    "🏰 @{user}, entre palacios de gloria y fosas de vergüenza 😏",
]

BOT_COMMENTS = [
    "Ja, esto es demasiado bueno 😏",
    "En serio… ¿alguien hace esto de verdad? 🙄",
    "Nivel ridículo detectado 😈",
    "Prepárense para reír (o llorar) 🤭",
    "¿Pensabas que lo olvidaría? Ja 😎",
]

ACCIONES = [
    "volo", "gano", "perdio", "choco", "salto", "corrio", "rompio",
    "grito", "lloro", "fallo", "aplasto", "esquivo", "ataco", "defendio",
    "piloto", "condujo", "abandono", "celebro", "insulto", "ignoro"
]

class SarcasticMemory(commands.Cog):
    def __init__(self, bot, memoria):
        self.bot = bot
        self.memoria = memoria

    @commands.command(name="soy")
    async def soy(self, ctx: commands.Context, *, contenido: str = None):
        user = ctx.author.name.lower()
        if not contenido:
            await ctx.send(f"@{user}, dime algo que guardar. Ej: !soy un manco")
            return
        contenido = contenido.strip()[:150]
        db.add_frase(user, contenido)
        await ctx.send(f"🧠 Anotado @{user}: *{contenido}* 😏")

    @commands.command(name="recuerda")
    async def recuerda(self, ctx: commands.Context, *, texto: str = None):
        if not texto:
            await ctx.send("⚡ !recuerda <usuario> <acción> en <lugar> 😈")
            return

        autor = ctx.author.name.lower()

        def normalize(s):
            s = s.lower()
            s = unicodedata.normalize("NFD", s)
            return "".join(c for c in s if unicodedata.category(c) != "Mn")

        texto_norm = normalize(texto)
        acciones_regex = "|".join(ACCIONES)
        pattern = fr"(\w+)\s+({acciones_regex})\s*(?:en\s+(.+))?"
        match = re.match(pattern, texto_norm)

        if match:
            sujeto, accion, lugar = match.groups()
            db.add_hecho(
                sujeto=sujeto,
                accion=accion,
                lugar=lugar if lugar else None,
                autor=autor
            )
            await ctx.send(f"🧠 Anotado: {sujeto} {accion}" + (f" en {lugar}" if lugar else "") + " 😏")
        else:
            db.add_recuerdo(autor, texto)
            await ctx.send(f"🧠 Guardado @{autor}: *{texto}* 😈")

    @commands.command(name="quiensoy")
    async def quiensoy(self, ctx: commands.Context, usuario: str = None):
        target_user = usuario.lower() if usuario else ctx.author.name.lower()
        await self._mini_relato_humano(ctx, target_user)

    @commands.command(name="quesabesde")
    async def quesabes(self, ctx: commands.Context, usuario: str = None):
        if not usuario:
            await ctx.send(f"@{ctx.author.name}, dime de quién quieres saber. Ej: !quesabesde fantan")
            return
        target_user = usuario.lstrip("@").lower()
        await self._mini_relato_humano(ctx, target_user)

    async def _mini_relato_humano(self, ctx, user):
        db.ensure_user_profile(user)

        frases = db.get_frases(user)
        recuerdos = db.get_recuerdos(user, max_items=5)
        hechos = db.get_hechos(user)

        if not frases and not recuerdos and not hechos:
            await ctx.send(f"@{ctx.author.name}, no sé nada de {user}… por ahora 😏")
            return

        relato = [random.choice(NARRATIVE_INTROS).format(user=user)]

        if frases:
            relato.append(f"Por cierto, {user} dijo: «{random.choice(frases)}»… {random.choice(BOT_COMMENTS)}")

        if recuerdos:
            seleccionados = random.sample(recuerdos, min(2, len(recuerdos)))
            textos = ", ".join(f"«{r['texto']}»" for r in seleccionados)
            relato.append(f"Recientemente comentó: {textos}… {random.choice(BOT_COMMENTS)}")

        if hechos:
            seleccionados = random.sample(hechos, min(2, len(hechos)))
            hechos_texto = ", ".join(
                f"{h['accion']}" + (f" en {h['lugar']}" if h['lugar'] else "")
                for h in seleccionados
            )
            relato.append(f"En su historial: {hechos_texto}… {random.choice(BOT_COMMENTS)}")

        relato.append(random.choice(SARCASTIC_OUTROS))

        mensaje_final = " | ".join(relato)[:350]
        await ctx.send(f"@{ctx.author.name} {mensaje_final}")