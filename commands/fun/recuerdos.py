from twitchio.ext import commands
import random

class Recuerdos(commands.Cog):

    def __init__(self, bot, memoria):
        self.bot = bot
        self.memoria = memoria

    @commands.command(name="recuerdos")
    async def recuerdos(self, ctx: commands.Context, user: str = None):
        """
        Muestra los recuerdos y frases de un usuario.
        """
        if not user:
            await ctx.send("😏 Con !recuerdos <usuario> puedes ver lo que @{usuario} dijo o dejó registrado… sí, cada frase random, cada momento de gloria o vergüenza 🤡")
            return

        user = user.lower()

        # Cargar datos del usuario
        frases = self.memoria.get_frases(user)  # Frases del perfil
        recuerdos = self.memoria.get_recuerdos(user, max=5)  # Recuerdos recientes

        if not frases and not recuerdos:
            await ctx.send(f"🤷 No recuerdo nada de {user}, ¿seguro que existe? 😂")
            return

        # ---------------- Plantillas ----------------
        recuerdos_templates = [
            "Ah sí, {} {}… impresionante, como siempre 😑",
            "No puedo olvidar cuando {} {}… qué nivel 😳",
            "Recuerdo que {} {}… épico, de verdad 😅",
            "Ah, {} {}… historia de nunca acabar 😏",
            "{} {}… y pensabas que nadie se daría cuenta 😬",
            "Ah sí, {} {}… qué desastre legendario 🤣",
            "Wow, {} {}… todavía no aprendes 😵",
            "{} {}… épico y patético al mismo tiempo 😎",
            "Ah, {} {}… digno de estudio 😂",
            "No puedo creer que {} {}… otra vez 😏",
            "{} {}… sigue coleccionando fails 😬",
            "Ah sí, {} {}… clásico del fracaso 🤡",
            "Recuerdo claramente {} {}… nivel experto 😑",
            "{} {}… otra joya de desastre 😅",
            "Ah, {} {}… digno de un meme viral 😂",
            "{} {}… y todavía sonríe como si nada 😎",
            "Ah sí, {} {}… otro episodio de torpeza 😏",
            "Increíble {} {}… desastre asegurado 😬",
            "{} {}… típico error, bravo 🤣",
            "Ah, {} {}… otra obra maestra del fail 😵",
            "Recuerdo que {} {}… memorable 😅",
            "{} {}… y nadie lo olvida 😑",
            "Ah sí, {} {}… sigue siendo épico 😂",
            "{} {}… y todavía cree que fue casualidad 😎",
            "No puedo olvidar {} {}… nivel desastre pro 😏",
            "{} {}… otro fail digno de aplausos 🤡",
            "Ah, {} {}… sigue acumulando historia 😬",
            "Recuerdo cuando {} {}… impresionante 😅",
            "{} {}… y pensabas que lo ibas a arreglar 😂",
            "Ah sí, {} {}… típico, sin sorpresas 😑",
            "{} {}… otra vez, igual de épico 😎",
            "Recuerdo {} {}… digno de estudio 🤣",
            "{} {}… sigue haciendo historia de fails 😏",
            "Ah, {} {}… nivel leyenda del desastre 😵",
            "{} {}… y nadie se sorprende 😅",
            "Recuerdo {} {}… memorable, de verdad 😂",
            "{} {}… y todavía lo niegas 😬",
            "Ah sí, {} {}… otro episodio hilarante 😎",
            "{} {}… digno de un capítulo épico 🤡",
            "Recuerdo {} {}… nivel épico y patético 😏",
            "{} {}… y todos lo recuerdan 😅",
            "Ah sí, {} {}… clásico histórico 😂",
            "{} {}… sigue acumulando fails 😬",
            "{} {}… memorable como siempre 😎",
            "Recuerdo {} {}… otro fail legendario 🤣",
            "{} {}… y todavía te sorprendes 😏",
            "Ah sí, {} {}… digno de estudio histórico 😵",
        ]


        frases_templates = [
            "Y por si alguien lo dudaba: '{}'… modestia cero 😎",
            "Otro ejemplo del ego de {}: '{}'… jajaja 🤣",
            "'{}'… sí, claro, muy humilde 😏",
            "Lo típico de {}: '{}'… impresionante 😅",
            "'{}'… ¿seguro que no quieres patentarlo? 😂",
            "Wow, '{}'… nivel de ego infinito 😎",
            "Ah sí, '{}'… y todavía presume 🤣",
            "'{}'… impresionante, como siempre 😏",
            "Otro clásico de {}: '{}'… nivel leyenda 😬",
            "'{}'… sí, claro, muy modesto 😅",
            "Ah, '{}'… digno de un meme 😂",
            "'{}'… y todos lo notan 😎",
            "Otro ejemplo de {}: '{}'… brillante pero arrogante 🤣",
            "'{}'… típico ego, bravo 😏",
            "Ah sí, '{}'… nivel épico de presunción 😬",
            "'{}'… y todavía se siente humilde 😅",
            "Otro clásico '{}'… modesto, sí, claro 😂",
            "'{}'… digno de estudio de ego 😎",
            "Ah, '{}'… impresionante, pero egocéntrico 🤣",
            "'{}'… y todos lo aplauden 😏",
            "Otro '{}'… nivel experto en presunción 😬",
            "'{}'… y todavía lo niega 😅",
            "Ah sí, '{}'… otro capítulo del ego 😂",
            "'{}'… digno de meme viral 😎",
            "Otro '{}'… nivel leyenda del ego 🤣",
            "'{}'… y todos lo recuerdan 😏",
            "Ah, '{}'… sigue presumiendo 😬",
            "'{}'… digno de estudio académico 😅",
            "Otro '{}'… modesto, como siempre 😂",
            "'{}'… impresionante nivel de presunción 😎",
            "Ah sí, '{}'… y todavía sonríe 🤣",
            "'{}'… típico de {}… ego nivel pro 😏",
            "Otro '{}'… digno de aplausos 😬",
            "'{}'… y nadie lo olvida 😅",
            "Ah, '{}'… otro capítulo épico 😂",
            "'{}'… nivel maestro del ego 😎",
            "Otro '{}'… impresionante pero arrogante 🤣",
            "'{}'… sigue presumiendo 😏",
            "Ah sí, '{}'… digno de estudio histórico 😬",
            "'{}'… típico ego legendario 😅",
            "Otro '{}'… y todavía presume 😂",
            "'{}'… impresionante como siempre 😎",
            "Ah, '{}'… digno de un meme viral 🤣",
            "'{}'… nivel experto en presunción 😏",
            "Otro '{}'… sigue acumulando ego 😬",
        ]


        # ---------------- Construir relato ----------------
        partes = []

        # Recuerdos
        for r in recuerdos:
            template = random.choice(recuerdos_templates)
            partes.append(template.format(user, r['texto']))

        # Frases del usuario
        for f in frases:
            template = random.choice(frases_templates)
            partes.append(template.format(user, f))

        # Mezclar para que no suene aburrido
        random.shuffle(partes)

        # Combinar en relato
        relato = " ... ".join(partes)

        # Limitar para Twitch (450 caracteres aprox.)
        if len(relato) > 450:
            relato = relato[:447] + "..."

        await ctx.send(f"🧠 Recuerdos de {user}: {relato}")
