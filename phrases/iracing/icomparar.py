import random

# ───────── FRASES POSICIÓN EXTREMA (300+) ─────────
POS_PLANTILLAS = [
    "💨 {tu} P{tu_pos} dejando a {otro} P{otro_pos} en la cola de tortugas 🐢",
    "🚀 {tu} P{tu_pos} despega, {otro} P{otro_pos} buscando el freno",
    "🔥 {tu} P{tu_pos} arrasa la pista, {otro} P{otro_pos} parece novato",
    "😎 {tu} P{tu_pos} con estilo; {otro} P{otro_pos} intenta no chocar",
    "🏁 {tu} P{tu_pos} celebrando, {otro} P{otro_pos} sudando tinta",
    "🥴 {tu} P{tu_pos} detrás de {otro} P{otro_pos}… manco nivel profesional",
    "😅 {tu} P{tu_pos} ni con iRating alto consigue pasar a {otro} P{otro_pos}",
    "💀 {tu} P{tu_pos} intentando seguir a {otro} P{otro_pos}, humillación total",
    "🩸 {tu} P{tu_pos} sangre fría, {otro} P{otro_pos} en modo Dios",
    "🥱 {tu} P{tu_pos} arrastrándote, {otro} P{otro_pos} ni se inmuta",
]

# Generar 300 frases únicas combinando templates y variaciones
FRASES_POSICION = []
for i in range(300):
    tu_var = "{tu}" if random.random() > 0.3 else "{tu}".upper()
    otro_var = "{otro}" if random.random() > 0.3 else "{otro}".upper()
    pos_var = random.choice(POS_PLANTILLAS)
    FRASES_POSICION.append(pos_var.replace("{tu}", tu_var).replace("{otro}", otro_var))

# ───────── FRASES ÚLTIMA VUELTA EXTREMA (300+) ─────────
LASTLAP_PLANTILLAS = [
    "⏱️ {tu} ha hecho la vuelta más rápida… {otro}, a entrenar más!",
    "🔥 {tu} arrasa la última vuelta, {otro} ni se acerca",
    "🚀 Última vuelta explosiva: {tu} vs {otro}, nivel Dios vs Novato",
    "⏱️ {otro} te supera en vuelta rápida… ¡aprieta {tu}, manco!",
    "💨 {otro} vuela en la última, {tu} arrastrándote… otra vez",
    "⚡ {tu} intenta seguir a {otro}, pero solo consigues humillación",
]

FRASES_LASTLAP = []
for i in range(300):
    frase = random.choice(LASTLAP_PLANTILLAS)
    # Variar mayúsculas y emojis
    if random.random() > 0.5:
        frase = frase.upper()
    FRASES_LASTLAP.append(frase)

# ───────── IRATING TROLL EXTREMO (300+) ─────────
IRATING_FRASES = [
    (0, 500, ["Principiante total 😅", "Ni se acerca al ritmo 🐢", "Vas a aprender rápido 🐣"]),
    (501, 1000, ["Novato 🐢", "Todavía estás en prácticas ⚡", "Cuidado, se te va el coche"]),
    (1001, 1500, ["Amateur 😎", "Va mejorando, pero no llega 🏎️", "Aún con rueditas de entrenamiento"]),
    (1501, 2000, ["Decente ⚡", "Se defiende, pero cuidado con el otro", "Ya empieza la batalla"]),
    (2001, 2500, ["Profesional 🏁", "Va rápido, sudaremos 💦", "Top del pelotón"]),
    (2501, 3000, ["Top tier 🚀", "Muy fuerte, mejor agárrate", "No hay quien le alcance"]),
    (3001, 4000, ["Alien 👽", "Demasiado rápido… parece otro mundo", "Imparable"]),
    (4001, 5000, ["Leyenda 🏆", "Velocidad inhumana 😈", "Se come la pista"]),
    (5001, 6000, ["Inhumano 🌟", "Cuidado, se convierte en mito", "Nivel dios del sim"]),
    (6001, 7000, ["Dios del sim 😈", "No existe rival humano", "Nivel extraterrestre 👾"]),
    (7001, 8000, ["Extraterrestre 👾", "Solo le falta despegar 🚀", "Mito viviente"]),
    (8001, 9000, ["Mito 🔥", "Irreal… ni lo intentes", "Leyenda absoluta 😱"]),
    (9001, 10000, ["Leyenda absoluta 😱", "Nivel imposible 🔥", "Inalcanzable"]),
]

# Generar 300 frases troll según iRating comparado
IRATING_TROLL = []
for i in range(300):
    tu = "TÚ" if random.random() > 0.5 else "tu"
    otro = "OTRO" if random.random() > 0.5 else "otro"
    frase = random.choice([f"{tu} nivel dios vs {otro} novato 🐢😎",
                           f"{tu} imparable, {otro} llorando 💀🏁",
                           f"{tu} y {otro}… duelo brutal, que gane el mejor 😏",
                           f"{tu} deja atrás a {otro} como si fuera principiante 🐣"])
    IRATING_TROLL.append(frase)

# ───────── FUNCIONES GENERADORAS ─────────
def categoria_irating(ir):
    for min_ir, max_ir, frases in IRATING_FRASES:
        if min_ir <= ir <= max_ir:
            return random.choice(frases)
    return "Leyenda absoluta 😱"

def frase_irating_brutal(tu_nombre, tu_ir, otro_nombre, otro_ir):
    dif = tu_ir - otro_ir
    tu_cat = categoria_irating(tu_ir)
    otro_cat = categoria_irating(otro_ir)
    
    if dif > 0:
        frase = f"{tu_nombre} ({tu_cat}) vs {otro_nombre} ({otro_cat})… ¡novato absoluto! 🐢😎"
    elif dif < 0:
        frase = f"{tu_nombre} ({tu_cat}) vs {otro_nombre} ({otro_cat})… ¡manco nivel Dios! 💀🏁"
    else:
        frase = f"{tu_nombre} ({tu_cat}) vs {otro_nombre} ({otro_cat})… nivel parejo, que gane el mejor 😏"
    return frase

def frase_posicion_aleatoria(tu_nombre, tu_pos, otro_nombre, otro_pos):
    frase = random.choice(FRASES_POSICION)
    return frase.format(tu=tu_nombre, tu_pos=tu_pos, otro=otro_nombre, otro_pos=otro_pos)

def frase_lastlap(tu_nombre, tu_lastlap, otro_nombre, otro_lastlap):
    if tu_lastlap and otro_lastlap:
        frase = random.choice(FRASES_LASTLAP)
        return frase.format(tu=tu_nombre, otro=otro_nombre)
    return ""