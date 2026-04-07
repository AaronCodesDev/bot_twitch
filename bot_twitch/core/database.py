# core/database.py
import sqlite3
import hashlib
import os
import threading
from datetime import datetime, date
from typing import Any, Dict, List, Optional

from core.config import DB_PATH

def _hash_password(password: str) -> str:
    return hashlib.sha256(password.encode("utf-8")).hexdigest()

class DatabaseManager:

    def __init__(self):
        os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)
        self._local = threading.local()

    def _get_conn(self) -> sqlite3.Connection:
        if not hasattr(self._local, "conn"):
            self._local.conn = sqlite3.connect(DB_PATH)
            self._local.conn.row_factory = sqlite3.Row
            self._local.conn.execute("PRAGMA foreign_keys = ON")
        return self._local.conn

    def _cursor(self):
        return self._get_conn().cursor()

    def _commit(self):
        self._get_conn().commit()

    def close(self):
        if hasattr(self._local, "conn"):
            self._local.conn.close()
            del self._local.conn

    # ==================== USUARIOS ====================

    def save_user(self, username: str, password: str, full_name: str = "",
                  email: str = "", ref_code: str = None, tier: int = 1):
        ref_code = ref_code or f"REF-{username.upper()}"
        self._cursor().execute("""
            INSERT INTO users (username, password, full_name, tier, email, ref_code)
            VALUES (?, ?, ?, ?, ?, ?)
            ON CONFLICT(username) DO UPDATE SET
                password=excluded.password,
                full_name=excluded.full_name,
                tier=excluded.tier,
                email=excluded.email,
                ref_code=excluded.ref_code
        """, (username, _hash_password(password), full_name, tier, email, ref_code))
        self._commit()

    def authenticate_user(self, username: str, password: str) -> Optional[Dict]:
        row = self._cursor().execute(
            "SELECT username, tier FROM users WHERE username=? AND password=?",
            (username, _hash_password(password))
        ).fetchone()
        return dict(row) if row else None

    def get_user(self, username: str) -> Optional[Dict]:
        row = self._cursor().execute(
            "SELECT * FROM users WHERE username=?", (username,)
        ).fetchone()
        return dict(row) if row else None

    def get_user_by_email(self, email: str) -> Optional[Dict]:
        row = self._cursor().execute(
            "SELECT * FROM users WHERE email=?", (email,)
        ).fetchone()
        return dict(row) if row else None

    def get_all_users(self) -> List[Dict]:
        rows = self._cursor().execute(
            "SELECT username, full_name, tier, ref_code FROM users ORDER BY tier DESC"
        ).fetchall()
        return [dict(r) for r in rows]

    def update_user(self, username: str, **kwargs):
        updates = []
        values = []
        for key, value in kwargs.items():
            if value is not None:
                if key == "password":
                    value = hashlib.sha256(value.encode("utf-8")).hexdigest()
                updates.append(f"{key}=?")
                values.append(value)
        if updates:
            values.append(username)
            self._cursor().execute(
                f"UPDATE users SET {', '.join(updates)} WHERE username=?",
                values
            )
            self._commit()

    def delete_user(self, username: str):
        self._cursor().execute("DELETE FROM users WHERE username=?", (username,))
        if username.lower() != "admin":
            self._cursor().execute("DELETE FROM user_config WHERE username=?", (username,))
        self._commit()

    # ==================== SUSCRIPTORES ====================

    def save_subscriber(self, username: str, tier: int = 1,
                        meses: int = 1, fecha: str = None):
        fecha = fecha or datetime.utcnow().isoformat()
        self._cursor().execute("""
            INSERT INTO subscribers (username, tier, meses, fecha)
            VALUES (?, ?, ?, ?)
            ON CONFLICT(username) DO UPDATE SET
                tier=excluded.tier,
                meses=excluded.meses,
                fecha=excluded.fecha
        """, (username, tier, meses, fecha))
        now = datetime.now()
        try:
            self._cursor().execute("""
                INSERT INTO subs_mensuales (username, tipo, meses, year, month, fecha)
                VALUES (?, 'normal', ?, ?, ?, ?)
                ON CONFLICT(username, tipo, year, month) DO UPDATE SET
                    meses=excluded.meses
            """, (username, meses, now.year, now.month, fecha))
        except:
            pass
        self._commit()

    def get_subscriber(self, username: str) -> Optional[Dict]:
        row = self._cursor().execute(
            "SELECT * FROM subscribers WHERE username=?", (username,)
        ).fetchone()
        return dict(row) if row else None

    def get_all_subscribers(self) -> List[Dict]:
        rows = self._cursor().execute(
            "SELECT * FROM subscribers ORDER BY tier DESC, meses DESC"
        ).fetchall()
        return [dict(r) for r in rows]

    def delete_subscriber(self, username: str):
        self._cursor().execute(
            "DELETE FROM subscribers WHERE username=?", (username,)
        )
        self._commit()

    # ==================== FAVORITOS ====================

    def save_favorito(self, nombre: str, contenido: str):
        self._cursor().execute("""
            INSERT INTO favoritos (nombre, contenido)
            VALUES (?, ?)
            ON CONFLICT(nombre) DO UPDATE SET contenido=excluded.contenido
        """, (nombre, contenido))
        self._commit()

    def get_favorito(self, nombre: str) -> Optional[Dict]:
        row = self._cursor().execute(
            "SELECT * FROM favoritos WHERE nombre=?", (nombre,)
        ).fetchone()
        return dict(row) if row else None

    def get_all_favoritos(self) -> List[Dict]:
        rows = self._cursor().execute(
            "SELECT * FROM favoritos ORDER BY nombre"
        ).fetchall()
        return [dict(r) for r in rows]

    def delete_favorito(self, nombre: str):
        self._cursor().execute(
            "DELETE FROM favoritos WHERE nombre=?", (nombre,)
        )
        self._commit()

    # ==================== IDEAS SORTEO ====================

    def save_idea(self, usuario: str, idea: str):
        self._cursor().execute(
            "INSERT INTO ideas (usuario, idea) VALUES (?, ?)",
            (usuario, idea)
        )
        self._commit()

    def get_all_ideas(self) -> List[Dict]:
        rows = self._cursor().execute(
            "SELECT * FROM ideas ORDER BY fecha"
        ).fetchall()
        return [dict(r) for r in rows]

    def clear_ideas(self):
        self._cursor().execute("DELETE FROM ideas")
        self._commit()

    # ==================== PERFILES Y FRASES ====================

    def ensure_user_profile(self, username: str):
        self._cursor().execute(
            "INSERT OR IGNORE INTO user_profiles (username) VALUES (?)",
            (username,)
        )
        self._commit()

    def add_frase(self, username: str, frase: str, confianza: int = 1):
        self.ensure_user_profile(username)
        self._cursor().execute(
            "INSERT OR IGNORE INTO user_frases (username, frase) VALUES (?, ?)",
            (username, frase)
        )
        self._cursor().execute(
            "UPDATE user_profiles SET confianza = confianza + ? WHERE username=?",
            (confianza, username)
        )
        self._commit()

    def get_frases(self, username: str) -> List[str]:
        rows = self._cursor().execute(
            "SELECT frase FROM user_frases WHERE username=?", (username,)
        ).fetchall()
        return [r["frase"] for r in rows]

    def get_confianza(self, username: str) -> int:
        row = self._cursor().execute(
            "SELECT confianza FROM user_profiles WHERE username=?", (username,)
        ).fetchone()
        return row["confianza"] if row else 0

    def add_confianza(self, username: str, valor: int):
        self.ensure_user_profile(username)
        self._cursor().execute(
            "UPDATE user_profiles SET confianza = confianza + ? WHERE username=?",
            (valor, username)
        )
        self._commit()

    # ==================== RECUERDOS ====================

    def add_recuerdo(self, username: str, texto: str):
        self.ensure_user_profile(username)
        hoy = date.today().isoformat()
        self._cursor().execute("""
            INSERT INTO recuerdos (username, texto, veces, ultima_vez)
            VALUES (?, ?, 1, ?)
            ON CONFLICT(username, texto) DO UPDATE SET
                veces = veces + 1,
                ultima_vez = excluded.ultima_vez
        """, (username, texto, hoy))
        self._commit()

    def get_recuerdos(self, username: str, max_items: int = 5) -> List[Dict]:
        rows = self._cursor().execute("""
            SELECT texto, veces, ultima_vez FROM recuerdos
            WHERE username=?
            ORDER BY ultima_vez DESC
            LIMIT ?
        """, (username, max_items)).fetchall()
        return [dict(r) for r in rows]

    # ==================== HECHOS ====================

    def add_hecho(self, sujeto: str, accion: str, lugar: str = None,
                  contexto: str = None, autor: str = None):
        self._cursor().execute("""
            INSERT INTO hechos (sujeto, accion, lugar, contexto, autor)
            VALUES (?, ?, ?, ?, ?)
        """, (sujeto, accion, lugar, contexto, autor))
        self._commit()

    def get_hechos(self, sujeto: str) -> List[Dict]:
        rows = self._cursor().execute(
            "SELECT * FROM hechos WHERE sujeto=? ORDER BY fecha", (sujeto,)
        ).fetchall()
        return [dict(r) for r in rows]

    # ==================== SUBS MENSUALES ====================

    def add_sub_mensual_normal(self, username: str, meses: int = 1,
                                year: int = None, month: int = None) -> bool:
        now = datetime.now()
        year = year or now.year
        month = month or now.month
        try:
            self._cursor().execute("""
                INSERT INTO subs_mensuales (username, tipo, meses, year, month, fecha)
                VALUES (?, 'normal', ?, ?, ?, ?)
            """, (username, meses, year, month, now.isoformat()))
            self._commit()
            return True
        except sqlite3.IntegrityError:
            return False

    def add_sub_mensual_regalo(self, gifter: str, receiver: str,
                                year: int = None, month: int = None) -> bool:
        now = datetime.now()
        year = year or now.year
        month = month or now.month
        try:
            self._cursor().execute("""
                INSERT INTO subs_mensuales (username, tipo, gifter, year, month, fecha)
                VALUES (?, 'regalada', ?, ?, ?, ?)
            """, (receiver, gifter, year, month, now.isoformat()))
            self._commit()
            return True
        except sqlite3.IntegrityError:
            return False

    def get_draw_pool(self, year: int, month: int) -> List[str]:
        rows = self._cursor().execute("""
            SELECT username, tipo, gifter FROM subs_mensuales
            WHERE year=? AND month=?
        """, (year, month)).fetchall()
        pool = []
        for r in rows:
            if r["tipo"] == "normal":
                pool.append(r["username"])
            elif r["tipo"] == "regalada":
                pool.append(r["gifter"])
        return pool

    # ==================== COMANDOS CUSTOM ====================

    def save_command(self, comando: str, respuesta: str, creado_by: str = None):
        self._cursor().execute("""
            INSERT INTO custom_commands (comando, respuesta, creado_by)
            VALUES (?, ?, ?)
            ON CONFLICT(comando) DO UPDATE SET
                respuesta=excluded.respuesta
        """, (comando, respuesta, creado_by))
        self._commit()

    def get_command(self, comando: str) -> Optional[str]:
        row = self._cursor().execute(
            "SELECT respuesta FROM custom_commands WHERE comando=?", (comando,)
        ).fetchone()
        return row["respuesta"] if row else None

    def get_all_commands(self) -> List[Dict]:
        rows = self._cursor().execute(
            "SELECT * FROM custom_commands ORDER BY comando"
        ).fetchall()
        return [dict(r) for r in rows]

    def delete_command(self, comando: str):
        self._cursor().execute(
            "DELETE FROM custom_commands WHERE comando=?", (comando,)
        )
        self._commit()

    # ==================== MÓDULOS ====================

    def is_module_enabled(self, module_name: str) -> bool:
        row = self._cursor().execute(
            "SELECT enabled FROM modules WHERE module_name=?", (module_name,)
        ).fetchone()
        return bool(row["enabled"]) if row else False

    def set_module_enabled(self, module_name: str, enabled: bool):
        self._cursor().execute("""
            INSERT INTO modules (module_name, enabled) VALUES (?, ?)
            ON CONFLICT(module_name) DO UPDATE SET enabled=excluded.enabled
        """, (module_name, int(enabled)))
        self._commit()

    # ==================== HISTORIAL COMANDOS ====================

    def log_command(self, username: str, comando: str, input: str = None, respuesta: str = None):
        self._cursor().execute("""
            INSERT INTO command_history (username, comando, input, respuesta)
            VALUES (?, ?, ?, ?)
        """, (username, comando, input, respuesta))
        self._commit()

    def get_command_history(self, username: str, max_items: int = 10) -> List[Dict]:
        rows = self._cursor().execute("""
            SELECT comando, input, respuesta, fecha FROM command_history
            WHERE username=?
            ORDER BY fecha DESC
            LIMIT ?
        """, (username, max_items)).fetchall()
        return [dict(r) for r in rows]

    # ==================== CONFIG POR USUARIO ====================

    def get_user_config(self, username: str) -> Optional[Dict]:
        row = self._cursor().execute(
            "SELECT * FROM user_config WHERE username=?", (username,)
        ).fetchone()
        return dict(row) if row else None

    def save_user_config(self, username: str, **kwargs):
        existing = self.get_user_config(username)
        if existing:
            updates = ", ".join(f"{k}=?" for k in kwargs)
            values = list(kwargs.values()) + [username]
            self._cursor().execute(
                f"UPDATE user_config SET {updates} WHERE username=?", values
            )
        else:
            kwargs["username"] = username
            cols = ", ".join(kwargs.keys())
            placeholders = ", ".join("?" * len(kwargs))
            self._cursor().execute(
                f"INSERT INTO user_config ({cols}) VALUES ({placeholders})",
                list(kwargs.values())
            )
        self._commit()

    def is_user_setup_done(self, username: str) -> bool:
        row = self._cursor().execute(
            "SELECT setup_done FROM user_config WHERE username=?", (username,)
        ).fetchone()
        return bool(row["setup_done"]) if row else False

    def migrate_admin_config(self, username: str, config: dict):
        existing = self.get_user_config(username)
        if existing and existing.get("setup_done"):
            return
        twitch = config.get("twitch", {})
        self.save_user_config(
            username=username,
            channel=twitch.get("channel", ""),
            bot_name=twitch.get("bot_name", ""),
            broadcaster_id=twitch.get("broadcaster_id", ""),
            token_bot=twitch.get("token_bot", ""),
            client_id_bot=twitch.get("client_id_bot", ""),
            token=twitch.get("token", ""),
            client_id=twitch.get("client_id", ""),
            client_secret=twitch.get("client_secret", ""),
            openai_api_key=config.get("openai", {}).get("api_key", ""),
            setup_done=1
        )
        print(f"✅ Config de {username} migrada a DB")


# Instancia global
db = DatabaseManager()