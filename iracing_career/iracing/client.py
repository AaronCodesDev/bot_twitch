"""
iracing/client.py — Cliente directo a la API de iRacing usando solo `requests`.
Sin iracingdataapi. Control total del flujo de autenticación y 2FA.

Flujo de auth:
  1. POST /auth  {email, sha256_hash}
     → OK:      {authcode: "...", ...}   → autenticado, cookies seteadas
     → 2FA:     {message: "...código...", authcode: 0 o ausente}
     → Error:   {message: "..."}
  2. POST /auth  {email, sha256_hash, code: "123456"}   (solo si 2FA)
     → OK:      {authcode: "...", ...}

Datos: GET /data/XXX → {link: "https://s3..."} → GET link → JSON real
"""

import os
import hashlib
import base64
import requests
from pathlib import Path
from urllib.parse import unquote

from dotenv import load_dotenv

_ENV_PATH = Path(__file__).parent.parent / ".env"
load_dotenv(_ENV_PATH, override=True)

_BASE   = "https://members-ng.iracing.com"
_session: requests.Session | None = None


# ── Utilidades ────────────────────────────────────────────────────────────────

def _hash_pw(password: str, username: str) -> str:
    return base64.b64encode(
        hashlib.sha256((password + username.lower()).encode("utf-8")).digest()
    ).decode("utf-8")


def _make_session() -> requests.Session:
    s = requests.Session()
    s.headers.update({
        "User-Agent": (
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
            "AppleWebKit/537.36 (KHTML, like Gecko) "
            "Chrome/124.0.0.0 Safari/537.36"
        ),
        "Accept":        "application/json",
        "Content-Type":  "application/json",
        "Referer":       "https://members-ng.iracing.com/",
    })
    return s


def reset_client() -> None:
    global _session
    _session = None


def _get(endpoint: str, params: dict = None) -> dict | list:
    """
    GET a un endpoint de la API de iRacing.
    iRacing devuelve {link: "..."} que hay que seguir para obtener los datos reales.
    """
    url = _BASE + endpoint
    r   = _session.get(url, params=params, timeout=15)
    r.raise_for_status()
    data = r.json()
    # Seguir el link firmado de S3 si viene
    if isinstance(data, dict) and "link" in data:
        r2 = _session.get(data["link"], timeout=15)
        r2.raise_for_status()
        return r2.json()
    return data


# ── Login ─────────────────────────────────────────────────────────────────────

def attempt_login(username: str, password: str) -> dict:
    """
    Primer paso del login.
    Devuelve:
      {"ok": True}
      {"needs_2fa": True, "msg": "..."}
      {"error": "..."}
    """
    global _session
    _session = _make_session()
    pw_hash  = _hash_pw(password, username)

    try:
        r = _session.post(
            f"{_BASE}/auth",
            json={"email": username, "password": pw_hash},
            timeout=15,
        )
    except requests.ConnectionError:
        return {"error": "Sin conexión a internet"}
    except requests.Timeout:
        return {"error": "Tiempo de espera agotado"}

    if not r.text.strip():
        return {"error": "iRacing no respondió (servidor caído o sin conexión)"}

    try:
        data = r.json()
    except Exception:
        return {"error": f"Respuesta inesperada de iRacing (HTTP {r.status_code})"}

    # Autenticado directamente
    if r.status_code == 200 and data.get("authcode"):
        return {"ok": True}

    # Requiere 2FA
    msg = str(data.get("message", "")).lower()
    if (
        "verif" in msg or "2fa" in msg or "code" in msg
        or data.get("verificationRequired")
        or data.get("needs_2fa")
        or data.get("authcode") == 0
    ):
        return {
            "needs_2fa": True,
            "msg": data.get("message", "Código enviado a tu email"),
        }

    return {"error": data.get("message", f"Login fallido (HTTP {r.status_code})")}


def submit_2fa(username: str, password: str, code: str) -> dict:
    """Segundo paso: enviar el código de 2FA."""
    global _session
    if _session is None:
        _session = _make_session()

    pw_hash = _hash_pw(password, username)

    try:
        r = _session.post(
            f"{_BASE}/auth",
            json={"email": username, "password": pw_hash, "code": code.strip()},
            timeout=15,
        )
    except Exception as e:
        return {"error": str(e)}

    if not r.text.strip():
        return {"error": "Sin respuesta de iRacing"}

    try:
        data = r.json()
    except Exception:
        return {"error": "Respuesta inválida"}

    if r.status_code == 200 and data.get("authcode"):
        return {"ok": True}

    return {"error": data.get("message", "Código incorrecto o expirado")}


def get_session() -> requests.Session:
    """
    Devuelve la sesión autenticada.
    Orden: usuario/contraseña → cookie de sesión (solo si es irsso real) → error.
    """
    global _session

    if _session is not None:
        return _session

    username = os.getenv("IRACING_USERNAME", "").strip()
    password = os.getenv("IRACING_PASSWORD", "").strip()
    cookie   = os.getenv("IRACING_COOKIE",   "").strip()

    if not username:
        raise RuntimeError("Sin credenciales. Ve a iR Career → Credenciales.")

    # ── Primero: usuario/contraseña (el método más fiable) ───────────────────
    if password:
        result = attempt_login(username, password)
        if result.get("ok"):
            return _session
        if result.get("needs_2fa"):
            raise RuntimeError("__NEEDS_2FA__")
        # Si falla con credenciales, intentar con cookie antes de rendirse
        if not cookie:
            raise RuntimeError(result.get("error", "Login fallido"))

    # ── Fallback: cookie de sesión irsso_membersv3 (2FA completado antes) ────
    # Solo usamos la cookie si parece una sesión real (>60 chars, no un hash)
    if cookie and len(unquote(cookie)) > 60:
        _session = _make_session()
        raw = unquote(cookie.strip().strip('"'))
        for domain in (".iracing.com", "members-ng.iracing.com"):
            _session.cookies.set("irsso_membersv3", raw, domain=domain)
        return _session

    raise RuntimeError("Sin credenciales válidas. Ve a iR Career → Credenciales.")


# ── Funciones de datos ────────────────────────────────────────────────────────

async def fetch_member_info() -> dict:
    try:
        get_session()
        data = _get("/data/stats/member_summary")
        if not data or "cust_id" not in data:
            reset_client()
            raise ValueError("Respuesta vacía — sesión expirada o credenciales incorrectas")
        return {
            "iracing_id": str(data.get("cust_id", "")),
            "name":       data.get("display_name", "Piloto"),
        }
    except RuntimeError:
        raise
    except Exception as e:
        reset_client()
        raise RuntimeError(str(e))


async def fetch_driver_stats(cust_id: int) -> dict:
    try:
        get_session()
        data     = _get("/data/member/profile", {"cust_id": cust_id})
        licenses = data.get("member", {}).get("licenses", []) if isinstance(data, dict) else []
        road     = next((l for l in licenses if l.get("category_id") == 2), {})
        return {
            "irating":       road.get("irating", 0),
            "safety_rating": round(road.get("safety_rating", 0.0) / 100, 2)
                             if road.get("safety_rating", 0) > 10 else road.get("safety_rating", 0.0),
            "license_class": road.get("license_letter", "?"),
            "category":      "Road",
        }
    except Exception:
        return {"irating": 0, "safety_rating": 0.0, "license_class": "?", "category": "Road"}


async def fetch_recent_results(cust_id: int, limit: int = 10) -> list[dict]:
    try:
        get_session()
        data  = _get("/data/stats/member_recent_races", {"cust_id": cust_id})
        races = (data.get("races", []) if isinstance(data, dict) else [])[:limit]
        out   = []
        for r in races:
            out.append({
                "subsession_id":   str(r.get("subsession_id", "")),
                "track":           r.get("track", {}).get("track_name", "Desconocido"),
                "series":          r.get("series_name", ""),
                "finish_position": r.get("finish_position", 0) + 1,
                "incidents":       r.get("incidents", 0),
                "irating_change":  r.get("newi_rating", 0) - r.get("oldi_rating", 0),
                "sr_change":       round(
                    (r.get("new_sub_level", 0) - r.get("old_sub_level", 0)) / 100, 2
                ),
                "prize_money": 0,
                "raced_at":    r.get("session_start_time", ""),
            })
        return out
    except Exception:
        return []
