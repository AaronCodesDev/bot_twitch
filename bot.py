import os
import json
import csv
import random
import re
import asyncio
from datetime import datetime, timedelta, timezone
from core.twitch_manager import TwitchManager
from core.iracing_listener import IRacingListener
from core.memory import Memory

# Librerías externas
import aiohttp
from twitchio.ext import commands
from openai import OpenAI
from phrases.bot.arrival import arrival_phrases
from phrases.social.hello import (
    answers_hello, answers_hello_favorites, answers_hello_neutral,
    answers_hello_subs, answers_hello_unfriendly
)
from phrases.social.subs import subs_gratitude_phrases, subs_hello_phrases, subs_phrases
from phrases.social.witty import witty_phrases, friendly_compliments_phrases, unfriendly_cheating_phrases
from phrases.social.wey import wey_normal_phrases, wey_estirado_phrases, wey_deformado_phrases

# --- CONSTANTES ---
DATA_FOLDER = 'data'
FAVORITOS_FILE = os.path.join(DATA_FOLDER, 'save/favoritos.json')
SUBS_FILE = os.path.join(DATA_FOLDER, 'subs/subscriptores_activos.json')
SUBS_MES_FILE = os.path.join(DATA_FOLDER, 'subs/')
IMPORT_FILE = os.path.join(DATA_FOLDER, 'imports/subscriber-list.csv')
CUENTA_PROPIA = 'fantan'

os.makedirs(DATA_FOLDER, exist_ok=True)
os.makedirs(SUBS_MES_FILE, exist_ok=True)
os.makedirs(os.path.dirname(IMPORT_FILE), exist_ok=True)

# --- CONFIGURACIÓN ---
with open('config.json', 'r', encoding='utf-8') as f:
    config = json.load(f)

client_openai = OpenAI(api_key=config["openai"]["api_key"])

# --- FUNCIONES GENERALES PARA JSON ---
def cargar_json(ruta, default=None):
    if default is None: default = {}
    if os.path.exists(ruta):
        try:
            with open(ruta, 'r', encoding='utf-8') as f:
                return json.load(f)
        except json.JSONDecodeError:
            return default
    return default

def guardar_json(ruta, datos):
    with open(ruta, 'w', encoding='utf-8') as f:
        json.dump(datos, f, indent=4, ensure_ascii=False)

# --- FAVORITOS Y SUSCRIPTORES ---
def cargar_favoritos(): return cargar_json(FAVORITOS_FILE, {})
def guardar_favoritos(favoritos): guardar_json(FAVORITOS_FILE, favoritos)

def cargar_suscriptores(): return cargar_json(SUBS_FILE, {})
def guardar_suscriptores(subs): guardar_json(SUBS_FILE, subs)

# --- IDEAS ---
IDEAS_FILE = os.path.join(DATA_FOLDER, 'save/ideas_sorteo.json')
def cargar_ideas(): return cargar_json(IDEAS_FILE, [])
def guardar_ideas(ideas): guardar_json(IDEAS_FILE, ideas)

# --- SUBSCRIPTORES ---
def guardar_sub(tipo, tier, usuario=None, regalador=None, receptor=None, blindado=True):
    ahora = datetime.now()
    mes = ahora.strftime("%Y-%m")
    fecha = ahora.strftime('%Y-%m-%d')
    archivo = f"{SUBS_MES_FILE}subs_{mes}.json"
    datos = cargar_json(archivo, {'normal': {}, 'regaladas': []})

    # --- Sub normal ---
    if tipo == 'normal' and usuario:
        if blindado:
            if usuario not in datos['normal']:
                datos['normal'][usuario] = 1
        else:
            datos['normal'][usuario] = datos['normal'].get(usuario, 0) + 1

    # --- Sub regalada ---
    elif tipo == 'regalada' and regalador and receptor:
        if not any(r['regalador']==regalador and r['receptor']==receptor and r['tier']==tier for r in datos['regaladas']):
            datos['regaladas'].append({'regalador': regalador, 'receptor': receptor, 'tier': tier, 'fecha': fecha})

    guardar_json(archivo, datos)

    # --- Actualizar subs activos ---
    subs = cargar_suscriptores()
    if tipo == 'normal' and usuario:
        if usuario not in subs or datetime.fromisoformat(subs[usuario]["fecha"]) < ahora:
            subs[usuario] = {'fecha': fecha, 'tier': tier}
    elif tipo == 'regalada' and receptor:
        if receptor not in subs or datetime.fromisoformat(subs[receptor]["fecha"]) < ahora:
            subs[receptor] = {'fecha': fecha, 'tier': tier}
    guardar_suscriptores(subs)

# --- IMPORTAR CSV DE TWITCH ---
def importar_subs_al_arrancar(blindado=True):
    """
    Importa el CSV de Twitch al sistema de subs históricos y subs activos.
    Crea archivos mensuales aunque no haya subs activos.
    También asegura que exista el archivo del mes actual.
    """
    # --- Asegurar archivo del mes actual ---
    ahora = datetime.now()
    mes_actual = ahora.strftime("%Y-%m")
    archivo_mes_actual = f"{SUBS_MES_FILE}subs_{mes_actual}.json"
    if not os.path.exists(archivo_mes_actual):
        guardar_json(archivo_mes_actual, {"normal": {}, "regaladas": []})
        print(f"ℹ️ Archivo del mes actual creado: {archivo_mes_actual}")

    if not os.path.exists(IMPORT_FILE):
        print("⚠️ No hay CSV de Twitch para importar")
        return

    print("🔄 Importando subs desde CSV...")

    activos_actualizados = {}

    with open(IMPORT_FILE, "r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        headers = reader.fieldnames or []

        es_csv_dashboard = "Username" in headers
        es_csv_api = "user_name" in headers

        if not es_csv_dashboard and not es_csv_api:
            print("⚠️ CSV desconocido")
            return

        for fila in reader:
            if es_csv_dashboard:
                usuario = fila.get("Username", "").lower()
                fecha_str = fila.get("Subscribe Date")
                tier_raw = fila.get("Current Tier", "Tier 1")
            else:
                usuario = fila.get("user_name", "").lower()
                fecha_str = fila.get("created_at")
                tier_raw = fila.get("tier", 1000)

            if not usuario or usuario == CUENTA_PROPIA:
                continue

            try:
                fecha_dt = datetime.fromisoformat(fecha_str.replace("Z", "+00:00"))
            except Exception:
                continue

            fecha_iso = fecha_dt.isoformat()
            mes_llave = fecha_dt.strftime("%Y-%m")

            if isinstance(tier_raw, str):
                tier = int(tier_raw.replace("Tier", "").strip())
            else:
                tier = int(tier_raw) // 1000

            # --- Crear archivo histórico mensual si no existe ---
            archivo_mes = f"{SUBS_MES_FILE}subs_{mes_llave}.json"
            datos = cargar_json(archivo_mes, {"normal": {}, "regaladas": []})

            if usuario not in datos["normal"]:
                datos["normal"][usuario] = 1
            elif not blindado:
                datos["normal"][usuario] += 1

            guardar_json(archivo_mes, datos)

            fecha_dt = datetime.fromisoformat(fecha_iso).replace(tzinfo=timezone.utc)
            
            # --- Guardar subs activos si no han expirado ---
            if (datetime.now(timezone.utc) - fecha_dt).days <= Memory.SUB_DURATION_DAYS:
                activos_actualizados[usuario] = {"fecha": fecha_iso, "tier": tier}

    # --- Guardar subs activos reemplazando expirados ---
    guardar_suscriptores(activos_actualizados)
    print("✅ Subs activos actualizados correctamente")
    print("✅ Importación histórica completada.")

# --- BOT ---
class BotFantan(commands.Bot):
    def __init__(self):
        super().__init__(token=config["twitch"]["token_bot"], prefix="!", initial_channels=[config["twitch"]["channel"]])
        self.config = config
        self.memory = Memory()
        self.favoritos = cargar_favoritos()
        self.suscriptores = cargar_suscriptores()
        self.current_game = None
        self.client_id = config["twitch"]["client_id"]
        self.client_secret = config["twitch"]["client_secret"]
        self.channel_id = config["twitch"]["broadcaster_id"]
        self.iracing_listener = None

        from commands.commands_list import lista_cogs
        for cog_cls in lista_cogs:
            if cog_cls.__name__ == "InstantGaming":
                self.add_cog(cog_cls(self, config=self.config, memory=self.memory))
            elif cog_cls.__name__ == "Opina":
                self.add_cog(cog_cls(self, client_openai, self.memory, config))
            elif "config" in cog_cls.__init__.__code__.co_varnames:
                self.add_cog(cog_cls(self, self.memory, config))
            else:
                self.add_cog(cog_cls(self, self.memory))

    # --- SUSCRIPTORES ---
    def es_suscriptor(self, usuario):
        usuario = usuario.lower()
        if usuario not in self.suscriptores:
            return False
        valor = self.suscriptores[usuario]
        fecha_str = valor.get("fecha") if isinstance(valor, dict) else str(valor)
        try:
            fecha_sub = datetime.fromisoformat(fecha_str)
        except Exception:
            return False
        return (datetime.utcnow() - fecha_sub).days <= Memory.SUB_DURATION_DAYS

    def es_viewer_favorito(self, usuario):
        return usuario.lower() in self.favoritos

    def obtener_nivel_trato(self, usuario):
        usuario = usuario.lower()
        if self.es_suscriptor(usuario): return "suscriptor"
        if self.es_viewer_favorito(usuario): return "favorito"
        confianza = self.memory.get_confianza(usuario)
        if confianza >= 1000: return "amigable"
        elif confianza >= 501: return "neutral"
        return "antipático"
    
    async def actualizar_csv_desde_twitch(self):
        try:
            manager = TwitchManager()
            exito = await manager.actualizar_csv_desde_twitch()
            if exito: print("✅ CSV actualizado correctamente desde Twitch.")
            return exito
        except Exception as e:
            print(f"❌ Error actualizando CSV desde Twitch: {e}")
            return False

    async def event_ready(self):
        print(f"✅ Bot conectado como {self.nick}!")
        frase = random.choice(arrival_phrases) if arrival_phrases else "¡Bot conectado!"
        for ch in self.connected_channels:
            await ch.send(frase)
        self.iracing_listener = IRacingListener(self)
        asyncio.create_task(self.iracing_listener.start())

    async def get_stream_info(self):
        headers = {'Client-ID': self.client_id, 'Authorization': f"Bearer {config['twitch']['token'].replace('oauth:', '')}"}
        url = f"https://api.twitch.tv/helix/channels?broadcaster_id={self.channel_id}"
        async with aiohttp.ClientSession() as session:
            async with session.get(url, headers=headers) as resp:
                data = await resp.json()
                if "data" in data and len(data["data"]) > 0:
                    info = data["data"][0]
                    return info.get("title", "Sin título"), info.get("game_name", "Sin juego")
        return None, None

    # --- EVENTOS DE SUBS ---
    async def event_subscription(self, channel, user, sub):
        guardar_sub('normal', sub.tier, usuario=user.name.lower())

    async def event_subgift(self, channel, gifter, user, sub):
        guardar_sub('regalada', sub.tier, regalador=gifter.name.lower(), receptor=user.name.lower())

    BOTS_IGNORADOS = {"bot_fantan", "moderadorbot", "nightbot", "streamelements"}

# --- EVENT MESSAGE ---
    async def event_message(self, message):
        if message.echo:
            return

        user = message.author.name.lower()
        if user in self.BOTS_IGNORADOS and message.author.is_mod:
            return

        texto = message.content.strip()
        self.memory.ensure_user(user)

        # --- COMANDOS NORMALES ---
        if texto.startswith("!"):

            # --- COMANDOS PERSONALIZADOS ---
            comando = texto[1:].split()[0].lower()
            custom = self.get_cog("CustomCommands")
            if custom and hasattr(custom, "custom_commands") and comando in custom.custom_commands:
                respuesta = custom.custom_commands[comando]
                respuesta = respuesta.replace("{user}", message.author.name)
                await message.channel.send(respuesta)
                return
            
            try:
                await self.handle_commands(message)
            except commands.errors.CommandNotFound:
                pass
            
        # --- MEMORIA ---
        self.memory.add_recuerdo(user, texto)

        # --- FILTRO DE SPAM ---
        palabras = texto.split()
        if len(texto) > 200 or (palabras and palabras.count(palabras[0]) > 5):
            await message.channel.send(f"@{user}, relaja el teclado 😏")
            self.memory.add_confianza(user, -3)
            return

        # --- FILTRO DE PALABROTAS ---
        if any(p in texto.lower() for p in ["noob", "mierda", "bot malo"]):
            await message.channel.send(f"@{user} cuidado con lo que dices 🤖💢")
            self.memory.add_confianza(user, -5)
            return

        # --- NIVEL DE CONFIANZA ---
        self.memory.add_confianza(user, +1)
        nivel = self.obtener_nivel_trato(user)

        respuestas_por_nivel = {
            "suscriptor": answers_hello_subs,
            "favorito": answers_hello_favorites,
            "amigable": answers_hello,
            "neutral": answers_hello_neutral,
            "antipático": answers_hello_unfriendly
        }

        # --- SALUDOS ---
        if re.search(r"\bhola\b", texto, re.IGNORECASE):
            saludo = random.choice(respuestas_por_nivel.get(nivel, answers_hello_unfriendly)).format(user=user)
            await message.channel.send(saludo)
            self.memory.add_comando(user, texto, cambio_confianza=2)

        # --- FRASES SEGÚN NIVEL ---
        config_trato = {
            "suscriptor": [(80, subs_gratitude_phrases, "halago"), (2, friendly_compliments_phrases, "pulla_extra")],
            "favorito": [(30, [f"¡@{user}, siempre es un placer verte por aquí! 💙",
                                f"¡Hey @{user}! ¡Me alegra que estés en el chat! 🌟"], "halago"),
                        (10, witty_phrases, "pulla")],
            "amigable": [(20, friendly_compliments_phrases, "halago")],
            "neutral": [(10, witty_phrases, "pulla")],
            "antipático": [(25, unfriendly_cheating_phrases, "pulla")]
        }

        rnd = random.randint(1, 100)
        for prob, lista, tipo in config_trato.get(nivel, []):
            if rnd <= prob:
                frase = random.choice(lista)
                await message.channel.send(f"@{user} {frase}")
                self.memory.add_comando(user, texto, cambio_confianza=2)
                break

        # --- RESPUESTAS WEY ---
        msg_lower = texto.lower()
        respuesta = None
        if re.search(r'\bw+e{2,}y+\b', msg_lower): respuesta = random.choice(wey_estirado_phrases)
        elif re.search(r'\bw+e+y+\b', msg_lower): respuesta = random.choice(wey_normal_phrases)
        elif re.search(r"\b[wvu]+[eéií]+[iy]+[y]+(?:s+)?\b", msg_lower):
            respuesta = random.choice(wey_deformado_phrases)
        if respuesta:
            await message.channel.send(f"@{user} {respuesta}")
            self.memory.add_comando(user, texto, cambio_confianza=2)



# --- PUNTO DE ENTRADA ---
if __name__ == "__main__":    
    bot = BotFantan()

    # 1️⃣ Crear archivo del mes actual si no existe
    ahora = datetime.now()
    mes_actual = ahora.strftime("%Y-%m")
    archivo_mes_actual = f"{SUBS_MES_FILE}subs_{mes_actual}.json"
    if not os.path.exists(archivo_mes_actual):
        guardar_json(archivo_mes_actual, {"normal": {}, "regaladas": []})
        print(f"ℹ️ Archivo del mes actual creado: {archivo_mes_actual}")

    # 2️⃣ Actualizar CSV desde Twitch
    asyncio.run(bot.actualizar_csv_desde_twitch())

    # 3️⃣ Importar subs y refrescar subs activos
    importar_subs_al_arrancar()

    # 4️⃣ Ejecutar bot
    bot.run()
