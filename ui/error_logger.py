# ui/error_logger.py
# Registro centralizado de errores — FanTan Hub
# Singleton que acumula errores de cualquier módulo y notifica al sidebar.

from datetime import datetime
from typing import Callable


class ErrorLogger:
    """
    Singleton de registro de errores.
    Cualquier módulo puede importar y usar get_logger() para añadir errores.
    La UI se suscribe con add_listener() para recibir notificaciones.
    """

    _instance: "ErrorLogger | None" = None

    def __new__(cls) -> "ErrorLogger":
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._entries: list[dict] = []
            cls._instance._listeners: list[Callable] = []
        return cls._instance

    # ─── API pública ──────────────────────────────────────────────────────────

    def log(self, source: str, message: str, detail: str = "") -> None:
        """Registra un error nuevo."""
        entry = {
            "ts":      datetime.now().strftime("%H:%M:%S"),
            "source":  source,
            "message": message,
            "detail":  detail,
        }
        self._entries.append(entry)
        self._notify()

    def get_all(self) -> list[dict]:
        """Devuelve todos los errores registrados (más reciente primero)."""
        return list(reversed(self._entries))

    def count(self) -> int:
        return len(self._entries)

    def clear(self) -> None:
        self._entries.clear()
        self._notify()

    # ─── Listeners ────────────────────────────────────────────────────────────

    def add_listener(self, fn: Callable) -> None:
        """Añade callback que se llama cuando hay un cambio (nuevo error o clear)."""
        if fn not in self._listeners:
            self._listeners.append(fn)

    def remove_listener(self, fn: Callable) -> None:
        if fn in self._listeners:
            self._listeners.remove(fn)

    def _notify(self) -> None:
        for fn in list(self._listeners):
            try:
                fn()
            except Exception:
                pass


def get_logger() -> ErrorLogger:
    """Devuelve la instancia global del logger."""
    return ErrorLogger()
