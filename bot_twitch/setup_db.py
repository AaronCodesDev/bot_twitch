# setup_db.py
import sqlite3
import os
import hashlib

from core.config import DB_PATH

def hash_password(password: str) -> str:
    return hashlib.sha256(password.encode("utf-8")).hexdigest()

def setup_database(force_reset=False):
    os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)

    if force_reset and os.path.exists(DB_PATH):
        os.remove(DB_PATH)
        print("🗑️ Base de datos anterior eliminada.")

    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("PRAGMA foreign_keys = ON")

    # ---------------- USUARIOS (login/admin) ----------------
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL,
            password TEXT NOT NULL,
            full_name TEXT,
            tier INTEGER DEFAULT 1,
            email TEXT UNIQUE,
            ref_code TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)

    # ---------------- SUSCRIPTORES ACTIVOS ----------------
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS subscribers (
            username TEXT PRIMARY KEY,
            tier INTEGER DEFAULT 1,
            meses INTEGER DEFAULT 1,
            fecha TEXT
        )
    """)

    # ---------------- FAVORITOS ----------------
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS favoritos (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            nombre TEXT UNIQUE NOT NULL,
            contenido TEXT NOT NULL,
            creado_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)

    # ---------------- IDEAS SORTEO ----------------
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS ideas (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            usuario TEXT NOT NULL,
            idea TEXT NOT NULL,
            fecha TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)

    # ---------------- PERFILES DE USUARIO ----------------
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS user_profiles (
            username TEXT PRIMARY KEY,
            confianza INTEGER DEFAULT 0,
            creado_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)

    # ---------------- FRASES !soy ----------------
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS user_frases (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT NOT NULL,
            frase TEXT NOT NULL,
            UNIQUE(username, frase)
        )
    """)

    # ---------------- RECUERDOS ----------------
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS recuerdos (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT NOT NULL,
            texto TEXT NOT NULL,
            veces INTEGER DEFAULT 1,
            ultima_vez TEXT NOT NULL,
            UNIQUE(username, texto)
        )
    """)

    # ---------------- HECHOS (!recuerda) ----------------
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS hechos (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            sujeto TEXT NOT NULL,
            accion TEXT NOT NULL,
            lugar TEXT,
            contexto TEXT,
            autor TEXT,
            fecha TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)

    # ---------------- SUBS MENSUALES ----------------
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS subs_mensuales (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT NOT NULL,
            tipo TEXT NOT NULL CHECK(tipo IN ('normal', 'regalada')),
            gifter TEXT,
            meses INTEGER DEFAULT 1,
            year INTEGER NOT NULL,
            month INTEGER NOT NULL,
            fecha TEXT NOT NULL,
            UNIQUE(username, tipo, year, month)
        )
    """)

    # ---------------- COMANDOS CUSTOM ----------------
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS custom_commands (
            comando TEXT PRIMARY KEY,
            respuesta TEXT NOT NULL,
            creado_by TEXT,
            creado_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)

    # ---------------- MÓDULOS ----------------
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS modules (
            module_name TEXT PRIMARY KEY,
            enabled INTEGER DEFAULT 1
        )
    """)

    # ---------------- HISTORIAL DE COMANDOS ----------------
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS command_history (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT NOT NULL,
            comando TEXT NOT NULL,
            input TEXT,
            respuesta TEXT,
            fecha TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)
    
    # ---------------- CONFIGURACIÓN POR USUARIO ----------------
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS user_config (
            username TEXT PRIMARY KEY,
            channel TEXT DEFAULT '',
            bot_name TEXT DEFAULT '',
            broadcaster_id TEXT DEFAULT '',
            token_bot TEXT DEFAULT '',
            client_id_bot TEXT DEFAULT '',
            token TEXT DEFAULT '',
            client_id TEXT DEFAULT '',
            client_secret TEXT DEFAULT '',
            openai_api_key TEXT DEFAULT '',
            setup_done INTEGER DEFAULT 0
        )
    """)

    # ---------------- DATOS INICIALES ----------------
    cursor.execute("""
        INSERT OR IGNORE INTO users (username, password, full_name, tier, email, ref_code)
        VALUES (?, ?, ?, ?, ?, ?)
    """, ("admin", hash_password("1234"), "Admin Principal", 3, "admin@bot.com", "MASTER_KEY"))

    modules_iniciales = [
        ("chat_logger",),
        ("sub_tracker",),
        ("iracing_monitor",),
        ("vending_manager",),
    ]
    cursor.executemany(
        "INSERT OR IGNORE INTO modules (module_name) VALUES (?)",
        modules_iniciales
    )

    conn.commit()
    conn.close()
    print("✅ Base de datos lista con todas las tablas.")
    print("👤 Usuario admin creado con tier 3.")

if __name__ == "__main__":
    setup_database(force_reset=False)