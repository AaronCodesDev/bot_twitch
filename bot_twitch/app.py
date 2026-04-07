# app.py
import os
import sys
import random
import re
import asyncio
import json
from datetime import datetime, timezone

from twitchio.ext import commands
from openai import OpenAI

from core.twitch_manager import TwitchManager
from core.iracing_listener import IRacingListener
from core.memory import Memory
from core.persistence import cargar_suscriptores, cargar_favoritos
from core.subs_manager import SubsManager
from core.database import db

from phrases.bot.arrival import arrival_phrases
from phrases.bot.exit import exit_phrases
from phrases.social.hello import (
    answers_hello, answers_hello_favorites, answers_hello_neutral,
    answers_hello_subs, answers_hello_unfriendly
)
from phrases.social.subs import subs_gratitude_phrases
from phrases.social.witty import witty_phrases, friendly_compliments_phrases, unfriendly_cheating_phrases
from phrases.social.wey import wey_normal_phrases, wey_estirado_phrases, wey_deformado_phrases

# --- CONFIGURACIÓN ---
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
CONFIG_PATH = os.path.join(BASE_DIR, "config.json")

with open(CONFIG_PATH, "r", encoding="utf-8") as f:
    config = json.load(f)

client_openai = OpenAI(api_key=config["openai"]["api_key"])

class BotFantan(commands.Bot):
    def __init__(self):
        super().__init__(
            token=config["twitch"]["token_bot"],
            prefix="!",
            initial_channels=[config["twitch"]["channel"]]
        )
        self.config = config
        self.memory = Memory()
        self.client_id = config["twitch"]["client_id"]
        self.channel_id = config["twitch"]["broadcaster_id"]
        self.iracing_listener = None
        self.BOTS_IGNORADOS = {"bot_fantan", "moderadorbot", "nightbot", "streamelements"}
        self._processed = set()

        from commands.commands_list import lista_cogs
        for cog_cls in lista_cogs:
            self._setup_cog(cog_cls)

    def _setup_cog(self, cog_cls):
        try:
            if cog_cls.__name__ == "InstantGaming":
                self.add_cog(cog_cls(self, config=self.config, memory=self.memory))
            elif cog_cls.__name__ == "Opina":
                self.add_cog(cog_cls(self, client_openai, self.memory, self.config))
            elif "config" in cog_cls.__init__.__code__.co_varnames:
                self.add_cog(cog_cls(self, self.memory, self.config))
            else:
                self.add_cog(cog_cls(self, self.memory))
        except Exception as e:
            print(f"❌ Error cargando el Cog {cog_cls.__name__}: {e}")

    def es_suscriptor(self, usuario):
        usuario = usuario.lower()
        sub = db.get_subscriber(usuario)
        if not sub:
            return False
        try:
            fecha_iso = sub["fecha"].replace("Z", "+00:00")
            fecha_sub = datetime.fromisoformat(fecha_iso)
            if fecha_sub.tzinfo is None:
                fecha_sub = fecha_sub.replace(tzinfo=timezone.utc)
            return (datetime.now(timezone.utc) - fecha_sub).days <= Memory.SUB_DURATION_DAYS
        except:
            return False

    def obtener_nivel_trato(self, usuario):
        usuario = usuario.lower()
        if self.es_suscriptor(usuario):
            return "suscriptor"
        if db.get_favorito(usuario):
            return "favorito"
        confianza = db.get_confianza(usuario)
        if confianza >= 1000:
            return "amigable"
        if confianza >= 501:
            return "neutral"
        return "antipático"

    async def event_ready(self):
        print(f"✅ Bot conectado como {self.nick}!")
        subs = db.get_all_subscribers()
        print(f"📊 [DATOS] Subs en memoria: {len(subs)}")
        frase = random.choice(arrival_phrases) if arrival_phrases else "¡Bot conectado!"
        for ch in self.connected_channels:
            await ch.send(frase)
        self.iracing_listener = IRacingListener(self)
        asyncio.create_task(self.iracing_listener.start())

    async def event_message(self, message):
        if message.echo or (message.author and message.author.name.lower() in self.BOTS_IGNORADOS):
            return

        # Evitar doble procesamiento
        msg_id = id(message)
        if msg_id in self._processed:
            return
        self._processed.add(msg_id)
        # Limpiar set para no acumular memoria
        if len(self._processed) > 1000:
            self._processed.clear()

        user = message.author.name.lower()
        texto = message.content.strip()

        self.memory.ensure_user(user)

        if texto.startswith("!"):
            print(f" [COMANDO] @{user} usó: {texto}")
            parts = texto[1:].split()
            if parts:
                comando_nombre = parts[0].lower()
                respuesta = db.get_command(comando_nombre)
                if respuesta:
                    respuesta = respuesta.replace("{user}", message.author.name)
                    await message.channel.send(respuesta)
                    return
            await self.handle_commands(message)
            return

        print(f" [CHAT] @{user}: {texto}")
        self.memory.add_recuerdo(user, texto)

        if await self._aplicar_filtros(message, user, texto):
            return

        await self._procesar_social(message, user, texto)

    async def event_command_error(self, ctx, error):
        if isinstance(error, commands.CommandNotFound):
            pass
        else:
            print(f"❌ Error en comando: {error}")

    async def _aplicar_filtros(self, message, user, texto):
        palabras = texto.split()
        if len(texto) > 200 or (palabras and palabras.count(palabras[0]) > 5):
            await message.channel.send(f"@{user}, relaja el teclado 😏")
            return True
        return False

    async def _procesar_social(self, message, user, texto):
        nivel = self.obtener_nivel_trato(user)
        self.memory.add_confianza(user, +1)
        if re.search(r"\bhola\b", texto, re.IGNORECASE):
            await self._enviar_saludo(message, user, nivel)
        await self._check_wey(message, user, texto)

    async def _enviar_saludo(self, message, user, nivel):
        dict_respuestas = {
            "suscriptor": answers_hello_subs,
            "favorito": answers_hello_favorites,
            "amigable": answers_hello,
            "neutral": answers_hello_neutral,
            "antipático": answers_hello_unfriendly
        }
        resp = random.choice(dict_respuestas.get(nivel, answers_hello_neutral)).format(user=user)
        await message.channel.send(resp)

    async def _check_wey(self, message, user, texto):
        msg = texto.lower()
        res = None
        if re.search(r'\bw+e{2,}y+\b', msg):
            res = random.choice(wey_estirado_phrases)
        elif re.search(r'\bw+e+y+\b', msg):
            res = random.choice(wey_normal_phrases)
        elif re.search(r"\b[wvu]+[eéií]+[iy]+[y]+(?:s+)?\b", msg):
            res = random.choice(wey_deformado_phrases)
        if res:
            await message.channel.send(f"@{user} {res}")


# --- APAGADO SEGURO ---
async def listen_for_exit(bot):
    loop = asyncio.get_event_loop()
    while True:
        line = await loop.run_in_executor(None, sys.stdin.readline)
        if "shutdown" in line.lower():
            print("💾 Orden de apagado recibida...")
            try:
                frase = random.choice(exit_phrases) if exit_phrases else "¡Me voy a descansar! Chau."
                for ch in bot.connected_channels:
                    await ch.send(f"[SISTEMA] {frase}")
            except:
                pass
            print("✅ Cerrando bot.")
            await bot.close()
            os._exit(0)


# --- PUNTO DE ENTRADA ---
if __name__ == "__main__":
    async def run_prep():
        print("🔄 Sincronizando sistema...")
        try:
            manager = SubsManager()
            await manager.actualizar_desde_twitch()
        except Exception as e:
            print(f"⚠️ Error en la sincronización inicial: {e}")

    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    loop.run_until_complete(run_prep())

    print("🚀 Iniciando Bot Fantan...")
    bot = BotFantan()
    loop.create_task(listen_for_exit(bot))
    bot.run()