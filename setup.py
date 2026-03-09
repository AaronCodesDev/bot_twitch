import os
import re
import json
import sys

# --- FUNCIONES DE APOYO ---

def get_input_multiline(prompt_text, current_value):
    """Muestra el valor actual y permite mantenerlo o cambiarlo."""
    print(f"\n👉 {prompt_text}:")
    print(f"   [Actual]: {current_value}")
    new_val = input(f"   (Escribe lo nuevo o pulsa Enter para mantener): ").strip()
    return new_val if new_val else current_value

def extract_phrases_from_file(file_path):
    """Extrae las frases de un archivo .py buscando contenido entre corchetes [ ]."""
    if not os.path.exists(file_path): return []
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
            match = re.search(r'=\s*\[(.*?)\]', content, re.DOTALL)
            if match:
                return re.findall(r'["\'](.*?)["\']', match.group(1))
    except: pass
    return []

def save_phrases_file(file_path, phrases):
    """Guarda las frases en el archivo con el formato original del bot."""
    var_name = os.path.basename(file_path).replace('.py', '').upper() + "_PHRASES"
    with open(file_path, 'w', encoding='utf-8') as f:
        f.write(f'{var_name} = [\n')
        for p in phrases:
            f.write(f'    "{p.replace('"', '\\"')}",\n')
        f.write(']\n')

def manage_list_editor(current_list, title):
    """Editor interactivo para listas (frases o admins)."""
    while True:
        os.system('cls' if os.name == 'nt' else 'clear')
        print(f"\n📂 EDITANDO: {title}")
        print("="*40)
        if not current_list:
            print("   (La lista está vacía)")
        else:
            for i, item in enumerate(current_list, 1):
                print(f"   {i}. {item}")
        print("="*40)
        print("   [a] Añadir | [e #] Eliminar número | [s] Salir")
        accion = input("\n👉 Opción: ").lower().strip()

        if accion == 's':
            break
        elif accion == 'a':
            nuevas = input("   Introduce nombres/frases (separadas por comas):\n   > ")
            if nuevas: current_list.extend([f.strip() for f in nuevas.split(',') if f.strip()])
        elif accion.startswith('e'):
            try:
                partes = accion.split()
                num = int(partes[1]) if len(partes) > 1 else int(input("   ¿Número a borrar?: "))
                if 1 <= num <= len(current_list): current_list.pop(num - 1)
            except: print("   ❌ No válido"); input("(Enter para continuar)")
    return current_list

# --- LÓGICA PRINCIPAL ---

def setup():
    print("\n" + "═"*50)
    print("🚀      CONFIGURADOR MAESTRO - BOT FANTAN      🚀")
    print("═"*50)

    # 1. CONFIG.JSON
    print("\n--- 🔑 SECCIÓN 1: CREDENCIALES Y ADMINS ---")
    conf = {"openai": {"api_key": "REPLACE_ME"}, "twitch": {}, "admin_users": ["REPLACE_ME"]}
    if os.path.exists('config.json'):
        with open('config.json', 'r', encoding='utf-8') as f:
            conf = json.load(f)

    conf['openai']['api_key'] = get_input_multiline("OpenAI API Key", conf['openai'].get('api_key', 'REPLACE_ME'))
    
    tw = conf['twitch']
    keys = ['token', 'channel', 'bot_name', 'client_id', 'client_secret', 'bot_id', 'client_id_bot', 'token_bot', 'broadcaster_id']
    for key in keys:
        tw[key] = get_input_multiline(f"Twitch {key.replace('_', ' ').title()}", tw.get(key, 'REPLACE_ME'))

    print("\n👥 Gestión de Administradores (admin_users)")
    if input("   ¿Quieres editar la lista de admins? [S/N]: ").lower() == 's':
        conf['admin_users'] = manage_list_editor(conf.get('admin_users', []), "USUARIOS ADMINISTRADORES")

    with open('config.json', 'w', encoding='utf-8') as f:
        json.dump(conf, f, indent=4, ensure_ascii=False)

    # 2. PERSONALIDAD (core/prompt.py) - BUSCADOR REFORZADO
    print("\n--- 🧠 SECCIÓN 2: PERSONALIDAD (PROMPT) ---")
    current_base = current_sub = current_fav = "No configurado"
    
    if os.path.exists('core/prompt.py'):
        with open('core/prompt.py', 'r', encoding='utf-8') as f:
            content = f.read()
            def find_p(v):
                # Este Regex ahora ignora espacios, saltos de línea y PARÉNTESIS opcionales
                # Busca: VARIABLE = ( opcional "texto" ) opcional
                pattern = rf'{v}\s*=\s*\(?\s*(?:"""|")(.*?)(?:"""|")\s*\)?'
                match = re.search(pattern, content, re.DOTALL)
                return match.group(1).strip() if match else "No configurado"
            
            current_base = find_p("SYSTEM_BASE")
            current_sub = find_p("SYSTEM_SUB")
            current_fav = find_p("SYSTEM_FAVORITO")

    base = get_input_multiline("Frase Base", current_base)
    sub = get_input_multiline("Frase Suscriptores", current_sub)
    fav = get_input_multiline("Frase Favoritos", current_fav)

    # Guardamos eliminando los paréntesis para que sea más limpio
    with open('core/prompt.py', 'w', encoding='utf-8') as f:
        f.write(f'SYSTEM_BASE = "{base}"\nSYSTEM_SUB = "{sub}"\nSYSTEM_FAVORITO = "{fav}"\n\n')
        f.write('def get_system_message(nivel: str) -> str:\n    if nivel == "suscriptor": return SYSTEM_SUB\n')
        f.write('    elif nivel == "favorito": return SYSTEM_FAVORITO\n    return SYSTEM_BASE\n\n')
        f.write('def build_user_message(user: str, contexto: str, texto: str) -> str:\n')
        f.write('    return (f"Diálogo previo con @{user}:\\n{contexto}\\n\\n" f"Mensaje actual: \\"{texto}\\"\\n" "⚠️ Responde en UNA sola frase corta y sarcástica.")\n')

    # 3. FRASES (phrases/)
    print("\n--- 🗣️ SECCIÓN 3: LIBRERÍA DE FRASES ---")
    if os.path.exists('phrases'):
        for root, _, files in os.walk('phrases'):
            for file in files:
                if file.endswith('.py') and not file.startswith('__'):
                    path = os.path.join(root, file)
                    print(f"\n📄 Archivo: {file}")
                    if input("   ¿Gestionar este archivo? [S/N]: ").lower() == 's':
                        phrases = extract_phrases_from_file(path)
                        new_phrases = manage_list_editor(phrases, f"FRASES EN {file}")
                        save_phrases_file(path, new_phrases)
    
    # 4. CARPETAS
    for d in ['data/users', 'data/subs', 'data/save', 'data/backup']: os.makedirs(d, exist_ok=True)
    print("\n" + "═"*50 + "\n✨ ¡LISTO! Todo configurado. 🏎️💨\n" + "═"*50)

if __name__ == "__main__":
    setup()