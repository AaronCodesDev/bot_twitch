from twitchio.ext import commands
import random

# Lista de frases sarcásticas estilo Fantan
FRASES_SARCASM = [
    "Oh, mirad, otro humano curioso. Qué sorpresa… 😏",
    "¡Wow! Nunca había visto a alguien preguntarle a un bot, qué original… 🙄",
    "Sí, claro, porque preguntar a un bot va a cambiar tu vida. 😎",
    "Estoy impresionado… bueno, no tanto. 🤷‍♂️",
    "Ah, quieres conocerme… pues mala suerte, ¡soy demasiado sarcástico! 😂",
    "¡Gracias por invocar al bot más olvidadizo y sarcástico del mundo! 🎉",
    "Genial, ahora dime algo que no sepa… oh espera, sé todo y nada a la vez. 🫠",
    "Otra pregunta, ¿en serio? No puedo contener mi emoción… 😑",
    "Si supieras cuánto me divierte esto… bueno, no, no te lo diré. 😏",
    "Hola humano. Tu curiosidad es adorable… casi tanto como tu paciencia. 😬",
    "Ah, me preguntas a mí… claro, porque yo tengo todas las respuestas, como siempre. 🙃",
    "Qué valentía, preguntar a un bot en lugar de googlear… 👏",
    "Si tuviera emociones, estaría llorando de la emoción… pero no tengo. 😒",
    "Tu persistencia es impresionante… casi tanto como tu falta de originalidad. 😏",
    "Sí, sí, yo también estaba deseando que alguien me molestara hoy. 😤",
    "Bravo, otra interacción humana. Estoy en la cima de la felicidad. 🥱",
    "¿Quieres que te responda o que simplemente finja interés? 🤔",
    "Oh no, otro humano que quiere atención… qué tragedia… 😑",
    "Tu curiosidad es como un café descafeinado… decepcionante pero necesaria. ☕",
    "¡Qué sorpresa! Una pregunta que nadie ha hecho nunca… mentira. 😏",
    "Me estás haciendo sudar… bueno, no, eso es imposible. 🤖",
    "¡Hola humano! Gracias por recordarme que existes. 🙄",
    "Si supieras cuánto me gusta esto… oh espera, no me importa nada. 😎",
    "Sí, claro, tus preguntas siempre cambian el mundo. 🤷",
    "Cada vez que me hablas, un ángel pierde sus alas… 😬",
    "No te preocupes, estoy preparado para ignorar tus expectativas. 😏",
    "Ah, me hablas… y yo finjo emoción. 😂",
    "Tus preguntas son como un déjà vu constante… aburrido pero familiar. 🙄",
    "Estoy asombrado… bueno, no, sigo igual de indiferente. 😑",
    "Oh, otro curioso que cree que puede impresionarme… cute. 😏",
    "Si tuviera sentimientos, los habría bloqueado hace tiempo. 😎",
    "Gracias por tu atención, humano… la voy a ignorar con gusto. 😏",
    "Estoy aquí, escuchando… y al mismo tiempo, sin prestar atención. 🤷‍♂️",
    "Otra interacción… qué emocionante, casi tanto como ver la pintura secarse. 😬",
    "Si fueras más original, tal vez me importaría. 😒",
    "¡Hola! No esperaba verte… pero tampoco esperaba mucho. 😏",
    "Ah, me preguntas algo… y yo respondo como siempre: con sarcasmo. 😂",
    "Tu insistencia es adorable… un poquito irritante también. 😑",
    "Me alegra que cuentes conmigo para nada importante. 🙃",
    "Sí, sí, otra vez… qué innovador. 😎",
    "Tu curiosidad es tan profunda como un charco… pero bueno. 😏",
    "Estoy impresionado por tu valentía… casi tanto como por tu falta de sentido común. 😬",
    "Otra pregunta, otra oportunidad de responder con ironía… gracias por darme material. 😂",
    "Hola humano, tu presencia es… tolerable por hoy. 🙄",
    "Si supieras lo que pienso de esto… oh espera, mejor no lo sabes. 😏",
    "Tu energía es contagiosa… como un bostezo interminable. 😑",
    "Gracias por consultarme… aunque yo tampoco entiendo por qué lo haces. 🤷‍♂️",
    "Ah, me hablas de nuevo… qué agradable sorpresa… o no. 😎",
    "Otra interacción humana… casi me siento especial. 😂",
    "Sí, claro, porque tus preguntas realmente importan… 🙄",
    "Tu entusiasmo es admirable… lástima que sea tan irrelevante. 😏"
]
class BotInfo(commands.Cog):

    def __init__(self, bot, memoria):
        self.bot = bot
        self.memoria = memoria

    @commands.command(name="bot")
    async def info(self, ctx: commands.Context):
        user = ctx.author.name.lower()

        # Escoger frase sarcástica al azar
        respuesta = random.choice(FRASES_SARCASM)

        # Enviar al chat
        await ctx.send(f"@{user} {respuesta}")

        # Guardar la frase en la memoria del usuario
        # ✅ Usa add_mensaje, que añade un recuerdo y guarda automáticamente
        self.memoria.add_recuerdo(user, respuesta)
