import json
import os
from datetime import datetime, date, timezone
from typing import Any, Dict, List, Optional

class Memory:
    SUB_DURATION_DAYS = 30
    MAX_RECUERDOS = 300

    def __init__(self, data_dir="data", debug=True):
        self.debug = debug
        if self.debug:
            print("🔥 MEMORY INIT:", id(self))

        self.data_dir = data_dir
        self.users_dir = os.path.join(self.data_dir, "users")
        self.subs_dir = os.path.join(self.data_dir, "subs")
        self.save_dir = os.path.join(self.data_dir, "save")

        os.makedirs(self.users_dir, exist_ok=True)
        os.makedirs(self.subs_dir, exist_ok=True)
        os.makedirs(self.save_dir, exist_ok=True)

        # Archivos principales
        self.favoritos_file = os.path.join(self.save_dir, "favoritos.json")
        self.subs_file = os.path.join(self.subs_dir, "subscriptores_activos.json")
        self.hechos_file = os.path.join(self.save_dir, "hechos.json")
        self.recuerdos_file = os.path.join(self.save_dir, "recuerdos.json")  # <-- archivo global

        # Cargar datos existentes
        self.favoritos: Dict[str, Any] = self._load(self.favoritos_file, {})
        self.subs: Dict[str, Any] = self._load(self.subs_file, {})
        self.hechos: List[Dict[str, Any]] = self._load(self.hechos_file, [])
        self.recuerdos_global: Dict[str, Dict[str, Any]] = self._load(self.recuerdos_file, {})

    # ------------------ Helpers ------------------
    def _user_path(self, user: str) -> str:
        return os.path.join(self.users_dir, f"{user.lower()}.json")

    def _load(self, path: str, default: Any) -> Any:
        if os.path.exists(path):
            try:
                with open(path, "r", encoding="utf-8") as f:
                    return json.load(f)
            except Exception:
                if self.debug:
                    print(f"⚠️ Error cargando JSON {path}, usando default")
        return default.copy() if isinstance(default, dict) else []

    def _save(self, path: str, data: Any):
        os.makedirs(os.path.dirname(path), exist_ok=True)
        tmp = path + ".tmp"
        with open(tmp, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=4, ensure_ascii=False)
        os.replace(tmp, path)
        if self.debug:
            print(f"💾 Guardado {path}")

    # ------------------ Hechos ------------------
    def add_hecho(self, sujeto, accion, lugar=None, contexto=None, autor=None):
        hecho = {
            "sujeto": sujeto.lower(),
            "accion": accion.lower(),
            "lugar": lugar.lower() if lugar else None,
            "contexto": contexto,
            "autor": autor,
            "fecha": datetime.now(timezone.utc).isoformat()
        }
        self.hechos.append(hecho)
        self._save(self.hechos_file, self.hechos)

    def buscar_hechos(self, sujeto):
        sujeto = sujeto.lower()
        return [h for h in self.hechos if h["sujeto"] == sujeto]

    # ------------------ Usuarios ------------------
    def ensure_user(self, user: str):
        user = user.lower()
        path = self._user_path(user)
        if not os.path.exists(path):
            data = {
                "perfil": {"soy": []},
                "recuerdos": {"mensaje": {}},
                "confianza": 0,
                "comandos": {},
            }
            self._save(path, data)

    def _load_user(self, user: str) -> Dict[str, Any]:
        self.ensure_user(user)
        return self._load(self._user_path(user), {})

    def _save_user(self, user: str, data: Dict[str, Any]):
        self._save(self._user_path(user), data)

    # ------------------ Frases (!soy) ------------------
    def add_frase(self, user: str, frase: str, confianza: int = 1):
        user = user.lower()
        data = self._load_user(user)
        soy = data.setdefault("perfil", {}).setdefault("soy", [])
        if frase not in soy:
            soy.append(frase)
            data["confianza"] = data.get("confianza", 0) + confianza
        self._save_user(user, data)

    def get_frases(self, user: str):
        """Devuelve la lista de frases (!soy) del usuario"""
        user = user.lower()
        data = self._load_user(user)
        return data.get("perfil", {}).get("soy", [])

    # ------------------ Recuerdos ------------------
    def add_recuerdo(self, user: str, texto: str):
        user = user.lower()
        texto = texto.strip()
        for char in ["\u200b", "\u200c", "\u200d", "\u2060", "͏"]:
            texto = texto.replace(char, "")
        if not texto:
            return

        # Guardar en archivo de usuario
        data = self._load_user(user)
        recuerdos = data.setdefault("recuerdos", {}).setdefault("mensaje", {})
        if texto in recuerdos:
            recuerdos[texto]["veces"] += 1
            recuerdos[texto]["ultima_vez"] = date.today().isoformat()
        else:
            recuerdos[texto] = {"veces": 1, "ultima_vez": date.today().isoformat()}

        if len(recuerdos) > self.MAX_RECUERDOS:
            sorted_items = sorted(recuerdos.items(), key=lambda x: x[1]["ultima_vez"])
            for k, _ in sorted_items[:-self.MAX_RECUERDOS]:
                del recuerdos[k]

        self._save_user(user, data)

        # Guardar en archivo global
        global_user = self.recuerdos_global.setdefault(user, {})
        global_user[texto] = recuerdos[texto]
        self._save(self.recuerdos_file, self.recuerdos_global)

    def get_recuerdos(self, user: str, max: int = 5):
        recuerdos = self._load_user(user).get("recuerdos", {}).get("mensaje", {})
        sorted_rec = sorted(recuerdos.items(), key=lambda x: x[1]["ultima_vez"], reverse=True)
        return [{"texto": k, **v} for k, v in sorted_rec[:max]]

    # ------------------ Comandos (!comando) ------------------
    def add_comando(self, user: str, comando: str, input_text: Optional[str] = None,
                     respuesta: Optional[str] = None, cambio_confianza: int = 0):
        if not comando.startswith("!"):
            return
        user = user.lower()
        data = self._load_user(user)
        cmds = data.setdefault("comandos", {}).setdefault(comando, [])
        entry = {"fecha": date.today().isoformat()}
        if input_text: entry["input"] = input_text
        if respuesta: entry["respuesta"] = respuesta
        cmds.append(entry)
        data["confianza"] = data.get("confianza", 0) + cambio_confianza
        self._save_user(user, data)

    # ------------------ Confianza ------------------
    def add_confianza(self, user: str, valor: int):
        user = user.lower()
        data = self._load_user(user)
        data["confianza"] = data.get("confianza", 0) + valor
        self._save_user(user, data)
        
    def get_confianza(self, user: str) -> int:
        """Devuelve la confianza actual del usuario"""
        user = user.lower()
        data = self._load_user(user)
        return data.get("confianza", 0)


    # ================== SUBS MENSUALES ==================

    def _monthly_subs_path(self, dt: datetime | None = None) -> str:
        dt = dt or datetime.now()
        return os.path.join(
            self.subs_dir,
            f"subs_{dt.year}-{dt.month:02d}.json"
        )

    def _load_monthly_subs(self, dt: datetime | None = None) -> Dict[str, Any]:
        dt = dt or datetime.now()
        path = self._monthly_subs_path(dt)
        default = {
            "normal": {},      # subs propias
            "regaladas": {}    # quien regala -> a quien
        }

        if not os.path.exists(path):
            self._save(path, default)
            return default

        return self._load(path, default)

    # ---------- Sub normal ----------
    def add_monthly_sub_normal(
        self,
        user: str,
        months: int | None = None,
        dt: datetime | None = None
    ):
        user = user.lower()
        dt = dt or datetime.now()

        data = self._load_monthly_subs(dt)

        # evitar duplicados el mismo mes
        if user in data["normal"]:
            return False

        data["normal"][user] = months or 1
        self._save(self._monthly_subs_path(dt), data)
        return True

    # ---------- Sub regalada ----------
    def add_monthly_sub_gift(
        self,
        gifter: str,
        receiver: str,
        dt: datetime | None = None
    ):
        gifter = gifter.lower()
        receiver = receiver.lower()
        dt = dt or datetime.now()

        data = self._load_monthly_subs(dt)

        gifts = data["regaladas"].setdefault(gifter, [])

        gifts.append({
            "a": receiver,
            "fecha": dt.date().isoformat()
        })

        self._save(self._monthly_subs_path(dt), data)
        return True

    # ---------- Pool para sorteos ----------
    def get_draw_pool(self, year: int, month: int) -> List[str]:
        path = os.path.join(self.subs_dir, f"subs_{year}-{month:02d}.json")
        if not os.path.exists(path):
            return []

        data = self._load(path, {})
        pool = []

        # subs propias → 1 participación
        pool.extend(data.get("normal", {}).keys())

        # subs regaladas → 1 participación por regalo
        for gifter, gifts in data.get("regaladas", {}).items():
            pool.extend([gifter] * len(gifts))

        return pool
