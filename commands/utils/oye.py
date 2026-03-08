from twitchio.ext import commands
import asyncio
from openai import OpenAI
from core.prompt import get_system_message, build_user_message


class Oye(commands.Cog):
    # Comandos oficiales que no se guardan como comandos
    COMANDOS_OFICIALES = ["!nivel", "!confianza", "!soy", "!quiensoy"]

    def __init__(self, bot, memoria, config):
        self.bot = bot
        self.memoria = memoria
        self.client_openai = OpenAI(api_key=config["openai"]["api_key"])

    # Nivel de trato del usuario
    def obtener_nivel_trato(self, user):
        user = user.lower()
        self.memoria.ensure_user(user)
        confianza = self.memoria.get_confianza(user)

        if user in self.memoria.subs:
            return "suscriptor"
        elif user in self.memoria.favoritos:
            return "favorito"
        elif confianza >= 10:
            return "amigo"
        else:
            return "normal"

    # Obtener comandos de un usuario
    def obtener_comandos_usuario(self, user):
        user = user.lower()
        self.memoria.ensure_user(user)
        data = self.memoria._load_user(user)
        return data.get("comandos", {})

    @commands.command(name="oye")
    async def oye(self, ctx: commands.Context, *, texto: str = None):
        user = ctx.author.name.lower()
        nivel = self.obtener_nivel_trato(user)

        if not texto:
            await ctx.send(f"@{user}, si vas a molestar al bot, al menos di algo.")
            return

        texto_limpio = texto.strip()

        # --- Guardar el !oye como comando ---
        comandos_actuales = self.obtener_comandos_usuario(user)
        if f"!oye {texto_limpio}" not in comandos_actuales:
            self.memoria.add_comando(user, f"!oye {texto_limpio}")

        # --- Guardar memoria ---
        if texto_limpio.lower().startswith("soy "):
            self.memoria.add_frase(user, texto_limpio)
        else:
            self.memoria.add_recuerdo(user, texto_limpio)

        # --- Contexto usuario ---
        if hasattr(self.memoria, "generar_contexto_usuario"):
            contexto = self.memoria.generar_contexto_usuario(user)
        else:
            contexto = "Sin contexto previo."

        # 🧠 Prompts externos
        system_message = get_system_message(nivel)
        user_message = build_user_message(user, contexto, texto_limpio)

        try:
            response = await asyncio.to_thread(
                self.client_openai.chat.completions.create,
                model="gpt-3.5-turbo",
                messages=[
                    {"role": "system", "content": system_message},
                    {"role": "user", "content": user_message},
                ],
                max_tokens=40,
                temperature=0.7 if nivel != "normal" else 0.8,
            )

            reply = response.choices[0].message.content.strip()

            await ctx.send(f"@{user} {reply}")

            # Guardar respuesta en historial
            self.memoria.add_comando(user, "!oye respuesta", respuesta=reply)

        except Exception as e:
            print(f"Error con OpenAI: {e}")
            await ctx.send(
                f"@{user}, estoy demasiado ocupado ignorándote ahora mismo. Intenta más tarde."
            )
