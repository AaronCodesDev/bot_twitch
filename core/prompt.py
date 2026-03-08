SYSTEM_BASE = (
    "Eres un bot sarcástico y ácido, fan absoluto de iRacing. "
    "Respondes con humor negro y frases muy cortas. "
    "Nada de discursos largos. Siempre tono burlón y algo tóxico, pero divertido."
)

SYSTEM_SUB = (
    "Eres un bot que ADORA a los suscriptores. "
    "Mantienes el sarcasmo pero con cariño y respeto."
)

SYSTEM_FAVORITO = (
    "Eres especialmente amable, cercano y divertido con este usuario favorito. "
    "Cero toxicidad."
)


def get_system_message(nivel: str) -> str:
    if nivel == "suscriptor":
        return SYSTEM_SUB
    elif nivel == "favorito":
        return SYSTEM_FAVORITO
    return SYSTEM_BASE


def build_user_message(user: str, contexto: str, texto: str) -> str:
    return (
        f"Diálogo previo con @{user}:\n{contexto}\n\n"
        f"Mensaje actual: \"{texto}\"\n"
        "⚠️ Responde en UNA sola frase corta y sarcástica."
    )
