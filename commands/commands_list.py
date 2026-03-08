# ───────── FUN ─────────
from .fun.charla import Charla
from .fun.excusa import Excusa
from .fun.frasejuego import FraseJuego
from .fun.gasolina import Gasolina
from .fun.iracingesmejor import IracingEsMejor
from .fun.lemas import Lemas
from .fun.opina import Opina
from .fun.sarcastic_memory import SarcasticMemory
from .fun.hechos import Hechos

# ───────── UTILS ─────────
from .utils.bot import BotInfo
from .utils.botcomandos import BotComandos
from .utils.instantgaming import InstantGaming
from .utils.modcomandos import ModComandos
from .utils.oye import Oye
from .utils.pregunta import Pregunta
from .utils.salir import Salir

# ───────── STATS ─────────
from .stats.comparar import Comparar
from .stats.confianza import Confianza
from .stats.ideas import Ideas
from .stats.nivel import Nivel
from .stats.nivelconfianza import NivelConfianza
from .stats.topamigables import TopAmigables

# ───────── TWITCH ─────────
from .twitch.clip import Clip
from .twitch.misub import MiSub
from .twitch.sorteo import Sorteo
from .twitch.subs import MostrarSubs
from .twitch.subsregaladas import SubsRegaladas
from .twitch.topregaladas import TopRegaladas
from .twitch.titulo_directo import TituloDirecto

# ───────── ADMIN ─────────
from .admin.actualizarsubs import ActualizarSubs
from .admin.ban import Ban
from .admin.promo import Promo

# ───────── DATABASE ─────────
from .database.guardar import Guardar
from .database.idea import Idea
from .database.olvidame import Olvidame
from .database.olvidarideas import OlvidarIdeas
from .database.olvidartodo import OlvidarTodo

# ───────── IRACING ─────────
from .iracing.carrera import Carrera
from .iracing.piloto import Piloto
from .iracing.pos import Pos
from .iracing.sof import SOF
from .iracing.icomparar import IComparar

# ───────── CUSTOM COMMANDS ─────────
from .customs.commands import CustomCommands

# ───────── COCKPIT ─────────
from .cockpit import Cockpit

# ───────── LISTA DE COGS ─────────
lista_cogs = [
    # FUN
    Charla,
    Excusa,
    FraseJuego,
    Gasolina,
    IracingEsMejor,
    Lemas,
    Opina,
    SarcasticMemory,
    Hechos,

    # UTILS
    BotInfo,
    BotComandos,
    InstantGaming,
    ModComandos,
    Oye,
    Pregunta,
    Salir,

    # STATS
    Comparar,
    Confianza,
    Ideas,
    Nivel,
    NivelConfianza,
    TopAmigables,

    # TWITCH
    Clip,
    MiSub,
    Sorteo,
    MostrarSubs,
    SubsRegaladas,
    TopRegaladas,
    TituloDirecto,

    # ADMIN
    ActualizarSubs,
    Ban,
    Promo,

    # DATABASE
    Guardar,
    Idea,
    Olvidame,
    OlvidarIdeas,
    OlvidarTodo,

    # IRACING
    Carrera,
    Piloto,
    Pos,
    SOF,
    IComparar,

    # CUSTOM COMMANDS
    CustomCommands,

    # COCKPIT
    Cockpit,
]