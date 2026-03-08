import os
import random
import re
import asyncio
import aiohttp
from datetime import datetime, timezone

from twitchio.ext import commands
from openai import OpenAI

# Imports de tu lógica separada en /core
from core.twitch_manager import TwitchManager
from core.iracing_listener import IRacingListener
from core.memory import Memory
from core.persistence import cargar_json, cargar_favoritos, cargar_suscriptores
from core.subs_manager import SubsManager

# Phrases
from phrases.bot.arrival import arrival_phrases
from phrases.social.hello import (
    answers_hello, answers_hello_favorites, answers_hello_neutral,
    answers_hello_subs, answers_hello_unfriendly
)
from phrases.social.subs import subs_gratitude_phrases
from phrases.social.witty import witty_phrases, friendly_compliments_phrases, unfriendly_cheating_phrases
from phrases.social.wey import wey_normal_phrases, wey_estirado_phrases, wey_deformado_phrases

# --- CONFIGURACIÓN ---
config = cargar_json('config.json')
client_openai = OpenAI(api_key=config["openai"]["api_key"])

class BotFantan(commands.Bot):
    def __init__(self):
        super().__init__(token=config["twitch"]["token_bot"], prefix="!", initial_channels=[config["twitch"]["channel"]])
        self.config = config
        self.memory = Memory()
        
        # Cargamos datos iniciales usando persistence
        self.favoritos = cargar_favoritos()
        self.suscriptores = cargar_suscriptores()
        
        self.client_id = config["twitch"]["client_id"]
        self.channel_id = config["twitch"]["broadcaster_id"]
        self.iracing_listener = None
        self.BOTS_IGNORADOS = {"bot_fantan", "moderadorbot", "nightbot", "streamelements"}

        # Carga de Cogs
        from commands.commands_list import lista_cogs
        for cog_cls in lista_cogs:
            self._setup_cog(cog_cls)

    def _setup_cog(self, cog_cls):
        """Lógica interna para registrar cogs según sus parámetros."""
        if cog_cls.__name__ == "InstantGaming":
            self.add_cog(cog_cls(self, config=self.config, memory=self.memory))
        elif cog_cls.__name__ == "Opina":
            self.add_cog(cog_cls(self, client_openai, self.memory, self.config))
        elif "config" in cog_cls.__init__.__code__.co_varnames:
            self.add_cog(cog_cls(self, self.memory, self.config))
        else:
            self.add_cog(cog_cls(self, self.memory))

    # --- LÓGICA DE USUARIOS ---
    def es_suscriptor(self, usuario):
        usuario = usuario.lower()
        if usuario not in self.suscriptores: return False
        
        info = self.suscriptores[usuario]
        fecha_str = info.get("fecha") if isinstance(info, dict) else str(info)
        try:
            fecha_sub = datetime.fromisoformat(fecha_str)
            return (datetime.now(timezone.utc) - fecha_sub.replace(tzinfo=timezone.utc)).days <= Memory.SUB_DURATION_DAYS
        except: return False

    def obtener_nivel_trato(self, usuario):
        usuario = usuario.lower()
        if self.es_suscriptor(usuario): return "suscriptor"
        if usuario in self.favoritos: return "favorito"
        
        confianza = self.memory.get_confianza(usuario)
        if confianza >= 1000: return "amigable"
        if confianza >= 501: return "neutral"
        return "antipático"

    # --- EVENTOS ---
    async def event_ready(self):
        print(f"✅ Bot conectado como {self.nick}!")
        frase = random.choice(arrival_phrases) if arrival_phrases else "¡Bot conectado!"
        for ch in self.connected_channels: await ch.send(frase)
        
        self.iracing_listener = IRacingListener(self)
        asyncio.create_task(self.iracing_listener.start())

    async def event_subscription(self, channel, user, sub):
        SubsManager.guardar_sub('normal', sub.tier, usuario=user.name.lower())

    async def event_subgift(self, channel, gifter, user, sub):
        SubsManager.guardar_sub('regalada', sub.tier, regalador=gifter.name.lower(), receptor=user.name.lower())

    async def event_message(self, message):
        if message.echo or message.author.name.lower() in self.BOTS_IGNORADOS:
            return

        user = message.author.name.lower()
        texto = message.content.strip()
        self.memory.ensure_user(user)

        # 1. Comandos
        if texto.startswith("!"):
            await self._handle_custom_and_standard_commands(message, texto)
            return

        # 2. Filtros y Memoria
        self.memory.add_recuerdo(user, texto)
        if await self._aplicar_filtros(message, user, texto): return

        # 3. Interacción Social
        await self._procesar_social(message, user, texto)

    async def _handle_custom_and_standard_commands(self, message, texto):
        comando = texto[1:].split()[0].lower()
        custom = self.get_cog("CustomCommands")
        if custom and hasattr(custom, "custom_commands") and comando in custom.custom_commands:
            await message.channel.send(custom.custom_commands[comando].replace("{user}", message.author.name))
        else:
            try: await self.handle_commands(message)
            except commands.errors.CommandNotFound: pass

    async def _aplicar_filtros(self, message, user, texto):
        """Retorna True si el mensaje fue filtrado por spam/insultos."""
        palabras = texto.split()
        if len(texto) > 200 or (palabras and palabras.count(palabras[0]) > 5):
            await message.channel.send(f"@{user}, relaja el teclado 😏")
            self.memory.add_confianza(user, -3)
            return True
        if any(p in texto.lower() for p in ["noob", "mierda", "bot malo"]):
            await message.channel.send(f"@{user} cuidado con lo que dices 🤖💢")
            self.memory.add_confianza(user, -5)
            return True
        return False

    async def _procesar_social(self, message, user, texto):
        nivel = self.obtener_nivel_trato(user)
        self.memory.add_confianza(user, +1)

        # Saludos
        if re.search(r"\bhola\b", texto, re.IGNORECASE):
            await self._enviar_saludo(message, user, nivel)

        # Respuestas "Wey"
        await self._check_wey(message, user, texto)

    async def _enviar_saludo(self, message, user, nivel):
        dict_respuestas = {
            "suscriptor": answers_hello_subs, "favorito": answers_hello_favorites,
            "amigable": answers_hello, "neutral": answers_hello_neutral, "antipático": answers_hello_unfriendly
        }
        resp = random.choice(dict_respuestas.get(nivel, answers_hello_neutral)).format(user=user)
        await message.channel.send(resp)

    async def _check_wey(self, message, user, texto):
        msg = texto.lower()
        res = None
        if re.search(r'\bw+e{2,}y+\b', msg): res = random.choice(wey_estirado_phrases)
        elif re.search(r'\bw+e+y+\b', msg): res = random.choice(wey_normal_phrases)
        elif re.search(r"\b[wvu]+[eéií]+[iy]+[y]+(?:s+)?\b", msg): res = random.choice(wey_deformado_phrases)
        
        if res: await message.channel.send(f"@{user} {res}")

# --- PUNTO DE ENTRADA ---
if __name__ == "__main__":
    bot = BotFantan()
    
    async def prep():
        # Llamamos al método estático del Manager, no al bot
        await SubsManager.actualizar_desde_twitch()
        # Luego importamos los datos
        SubsManager.importar_subs_al_arrancar()
    
    # Ejecutar la preparación
    try:
        loop = asyncio.get_event_loop()
        loop.run_until_complete(prep())
    except Exception as e:
        print(f"⚠️ Error en la preparación inicial: {e}")

    # Lanzar el bot
    bot.run()