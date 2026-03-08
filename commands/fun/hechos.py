from twitchio.ext import commands
import random

class Hechos(commands.Cog):

    def __init__(self, bot, memoria):
        self.bot = bot
        self.memoria = memoria

    @commands.command(name="hechos")
    async def hechos(self, ctx: commands.Context, user: str = None):
        if not user:
            await ctx.send(
                "😏 Con !hechos <usuario> puedes ver todos los gloriosos desastres que ha protagonizado… sí, cada tropezón, cada bochorno, todo recopilado para tu entretenimiento 🤡"
            )
            return

        user = user.lower()

        hechos = self.memoria.buscar_hechos(user)
        if not hechos:
            await ctx.send(f"🤷 No recuerdo ningún hecho de {user}, ¿seguro que existe? 😂")
            return

        # ---------------- Plantillas de hechos ----------------
        hechos_templates = [
            "{} {} en {}… vaya, no me lo esperaba 😏",
            "¿En serio {} {} en {}? 😂 desastre anunciado!",
            "{} {} en {}… y todavía se sorprende 🤡",
            "Ah, {} {} en {}… típico, no falla 😬",
            "{} {} en {}… otro día más, otra metedura de pata 😵",
            "{} {} en {}… y todavía se cree listo 😑",
            "Wow, {} {} en {}… no lo vi venir, mentira 😅",
            "Ah sí, {} {} en {}… como si fuera novedad 😏",
            "{} {} en {}… qué nivel de torpeza 🤣",
            "Increíble, {} {} en {}… desastre épico 😎",
            "{} {} en {}… bravo, lo lograste otra vez 😬",
            "No puedo con {} {} en {}… típico desastre 🤡",
            "{} {} en {}… y nadie se sorprende 😑",
            "Genial, {} {} en {}… qué originalidad 😂",
            "{} {} en {}… así es como arruinas todo 😵",
            "Otra vez {} {} en {}… ¡sin palabras! 😅",
            "Increíblemente, {} {} en {}… otro fail 🤣",
            "{} {} en {}… y aún sonríe como si nada 😏",
            "Ah, {} {} en {}… clásico, predecible 😬",
            "{} {} en {}… qué sorpresa… no 😑",
            "Vaya {} {} en {}… digno de un meme 🤡",
            "{} {} en {}… y todavía se queja 😂",
            "Fabuloso, {} {} en {}… desastre nivel pro 😎",
            "{} {} en {}… como si no aprendiera nunca 😵",
            "Ah sí, {} {} en {}… otro capítulo de su serie de fails 😅",
            "{} {} en {}… y lo vuelve a hacer 😏",
            "{} {} en {}… épico, pero malo 😬",
            "Bravo {} {} en {}… desastre asegurado 🤣",
            "{} {} en {}… todavía cree que es casualidad 😑",
            "{} {} en {}… me deja sin palabras 😵",
            "Ah, {} {} en {}… otra obra maestra de desastre 😅",
            "{} {} en {}… y todavía sonría 🤡",
            "Increíble {} {} en {}… digno de estudio 😂",
            "{} {} en {}… nivel experto en meteduras de pata 😏",
            "Ah, {} {} en {}… y todavía se sorprende 😬",
            "{} {} en {}… otro fail memorable 😎",
            "{} {} en {}… como siempre, desastre total 🤣",
            "{} {} en {}… otra vez, sin aprender 😑",
            "Wow, {} {} en {}… qué clase de talento 🤡",
            "{} {} en {}… típico error, bravo 😅",
            "{} {} en {}… nivel desastre pro 😂",
            "Ah, {} {} en {}… qué originalidad 😏",
            "{} {} en {}… y sigue intentando 😬",
            "{} {} en {}… digno de un meme viral 🤣",
            "{} {} en {}… sigue acumulando fails 😵",
            "{} {} en {}… otro día, otra metedura de pata 😅",
            "{} {} en {}… épico pero inútil 😎",
            "{} {} en {}… y aún se cree héroe 🤡",
            "{} {} en {}… desastre asegurado, sin sorpresa 😑",
            "{} {} en {}… y todavía piensa que no pasa nada 😂",
        ]

        # Construir relatos
        relatos = []
        for h in hechos:
            lugar = h.get('lugar', "algún sitio misterioso")
            template = random.choice(hechos_templates)
            relatos.append(template.format(h['sujeto'], h['accion'], lugar))

        random.shuffle(relatos)
        relato = " ... ".join(relatos)
        if len(relato) > 450:
            relato = relato[:447] + "..."

        await ctx.send(f"🧠 Hechos de {user}: {relato}")
