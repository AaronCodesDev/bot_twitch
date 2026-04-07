# migrate.py
import json
import os
import glob
from datetime import datetime
from core.database import db

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_DIR = os.path.join(BASE_DIR, "data")

def migrar_favoritos():
    path = os.path.join(DATA_DIR, "save", "favoritos.json")
    if not os.path.exists(path):
        print("⚠️  favoritos.json no encontrado, saltando.")
        return
    with open(path, "r", encoding="utf-8") as f:
        data = json.load(f)
    count = 0
    for nombre, contenido in data.items():
        db.save_favorito(nombre.lower(), contenido)
        count += 1
    print(f"✅ Favoritos migrados: {count}")

def migrar_ideas():
    path = os.path.join(DATA_DIR, "save", "ideas_sorteo.json")
    if not os.path.exists(path):
        print("⚠️  ideas_sorteo.json no encontrado, saltando.")
        return
    with open(path, "r", encoding="utf-8") as f:
        data = json.load(f)
    count = 0
    for item in data:
        db.save_idea(
            usuario=item.get("usuario", "unknown").lower(),
            idea=item.get("idea", "")
        )
        count += 1
    print(f"✅ Ideas migradas: {count}")

def migrar_subscribers():
    path = os.path.join(DATA_DIR, "subs", "subscriptores_activos.json")
    if not os.path.exists(path):
        print("⚠️  subscriptores_activos.json no encontrado, saltando.")
        return
    with open(path, "r", encoding="utf-8") as f:
        data = json.load(f)
    count = 0
    for username, info in data.items():
        db.save_subscriber(
            username=username.lower(),
            tier=info.get("tier", 1),
            meses=info.get("meses", 1),
            fecha=info.get("fecha", None)
        )
        count += 1
    print(f"✅ Suscriptores migrados: {count}")

def migrar_usuarios():
    users_dir = os.path.join(DATA_DIR, "users")
    if not os.path.exists(users_dir):
        print("⚠️  Carpeta data/users no encontrada, saltando.")
        return
    archivos = glob.glob(os.path.join(users_dir, "*.json"))
    count = 0
    for archivo in archivos:
        username = os.path.splitext(os.path.basename(archivo))[0].lower()
        with open(archivo, "r", encoding="utf-8") as f:
            try:
                data = json.load(f)
            except json.JSONDecodeError:
                print(f"⚠️  Error leyendo {archivo}, saltando.")
                continue

        # Perfil y confianza
        db.ensure_user_profile(username)
        confianza = data.get("confianza", 0)
        if confianza > 0:
            db.add_confianza(username, confianza)

        # Frases !soy
        frases = data.get("perfil", {}).get("soy", [])
        for frase in frases:
            db._cursor().execute(
                "INSERT OR IGNORE INTO user_frases (username, frase) VALUES (?, ?)",
                (username, frase)
            )
        db._commit()

        # Recuerdos
        recuerdos = data.get("recuerdos", {}).get("mensaje", {})
        for texto, info in recuerdos.items():
            db._cursor().execute("""
                INSERT INTO recuerdos (username, texto, veces, ultima_vez)
                VALUES (?, ?, ?, ?)
                ON CONFLICT(username, texto) DO UPDATE SET
                    veces=excluded.veces,
                    ultima_vez=excluded.ultima_vez
            """, (username, texto, info.get("veces", 1), info.get("ultima_vez", datetime.now().date().isoformat())))
        db._commit()
        count += 1

    print(f"✅ Usuarios migrados: {count}")

def migrar_hechos():
    path = os.path.join(DATA_DIR, "save", "hechos.json")
    if not os.path.exists(path):
        print("⚠️  hechos.json no encontrado, saltando.")
        return
    with open(path, "r", encoding="utf-8") as f:
        data = json.load(f)
    count = 0
    for hecho in data:
        db.add_hecho(
            sujeto=hecho.get("sujeto", "").lower(),
            accion=hecho.get("accion", "").lower(),
            lugar=hecho.get("lugar"),
            contexto=hecho.get("contexto"),
            autor=hecho.get("autor")
        )
        count += 1
    print(f"✅ Hechos migrados: {count}")

def migrar_subs_mensuales():
    subs_dir = os.path.join(DATA_DIR, "subs")
    archivos = glob.glob(os.path.join(subs_dir, "subs_*.json"))
    if not archivos:
        print("⚠️  No se encontraron archivos de subs mensuales, saltando.")
        return
    count = 0
    for archivo in archivos:
        # Extraer year y month del nombre: subs_2026-03.json
        nombre = os.path.splitext(os.path.basename(archivo))[0]
        try:
            _, ym = nombre.split("_", 1)
            year, month = map(int, ym.split("-"))
        except ValueError:
            print(f"⚠️  No se pudo parsear {archivo}, saltando.")
            continue

        with open(archivo, "r", encoding="utf-8") as f:
            try:
                data = json.load(f)
            except json.JSONDecodeError:
                continue

        for username, meses in data.get("normal", {}).items():
            db.add_sub_mensual_normal(username.lower(), meses=meses, year=year, month=month)
            count += 1

        for gifter, gifts in data.get("regaladas", {}).items():
            for gift in gifts:
                db.add_sub_mensual_regalo(
                    gifter=gifter.lower(),
                    receiver=gift.get("a", "").lower(),
                    year=year,
                    month=month
                )
                count += 1

    print(f"✅ Subs mensuales migradas: {count} registros")

def migrar_commands():
    path = os.path.join(DATA_DIR, "custom_commands", "commands.json")
    if not os.path.exists(path):
        print("⚠️  commands.json no encontrado, saltando.")
        return
    with open(path, "r", encoding="utf-8") as f:
        data = json.load(f)
    count = 0
    for comando, respuesta in data.items():
        db.save_command(comando.lower(), respuesta)
        count += 1
    print(f"✅ Comandos custom migrados: {count}")

if __name__ == "__main__":
    print("🚀 Iniciando migración de JSON a SQLite...\n")
    migrar_favoritos()
    migrar_ideas()
    migrar_subscribers()
    migrar_usuarios()
    migrar_hechos()
    migrar_subs_mensuales()
    migrar_commands()
    print("\n✅ Migración completada. Los JSON originales no han sido tocados.")
    print("💡 Cuando compruebes que todo está bien, puedes borrarlos.")