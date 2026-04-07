# gui/services/user_service.py
import hashlib
from core.database import db

def _hash_password(password: str) -> str:
    return hashlib.sha256(password.encode()).hexdigest()


class UserService:

    def register(self, username: str, password: str, full_name: str = "",
                 email: str = "", ref_code: str = None, tier: int = 1):
        try:
            db.save_user(username, password, full_name, email, ref_code, tier)
            return True
        except Exception as e:
            print(f"Error en registro: {e}")
            return False

    def get_profile(self, username: str):
        user = db.get_user(username.lower())
        if user:
            return {
                "full_name": user.get("full_name") or "",
                "email": user.get("email") or "",
                "ref_code": user.get("ref_code") or "",
                "tier": user.get("tier", 1)
            }
        return {"full_name": "", "email": "", "ref_code": "", "tier": 1}

    def get_all_users(self):
        users = db.get_all_users()
        return [(u["username"], u["full_name"], u["tier"], u["ref_code"]) for u in users]

    def update_profile(self, username: str, name: str = None, email: str = None,
                       password: str = None, ref_code: str = None):
        try:
            kwargs = {}
            if name is not None: kwargs["full_name"] = name
            if email is not None: kwargs["email"] = email
            if ref_code is not None: kwargs["ref_code"] = ref_code
            if password: kwargs["password"] = _hash_password(password)
            if kwargs:
                db.update_user(username.lower(), **kwargs)
            return True
        except Exception as e:
            print(f"Error updating profile: {e}")
            return False

    def update_user(self, username: str, tier: int = None, full_name: str = None,
                    email: str = None, password: str = None, ref_code: str = None):
        try:
            kwargs = {}
            if tier is not None: kwargs["tier"] = tier
            if full_name is not None: kwargs["full_name"] = full_name
            if email is not None: kwargs["email"] = email
            if ref_code is not None: kwargs["ref_code"] = ref_code
            if password: kwargs["password"] = _hash_password(password)
            if kwargs:
                db.update_user(username.lower(), **kwargs)
            return True
        except Exception as e:
            print(f"Error updating user: {e}")
            return False

    def delete_user(self, username: str, current_user: str):
        try:
            username = username.lower()
            current_user = current_user.lower()
            if username == current_user:
                return False, "No puedes eliminar tu propia cuenta"
            if not db.get_user(username):
                return False, "El usuario no existe"
            db.delete_user(username)
            return True, f"Usuario {username} eliminado correctamente"
        except Exception as e:
            return False, f"Error al eliminar: {str(e)}"

    def authenticate(self, username: str, password: str):
        return db.authenticate_user(username.lower(), password)