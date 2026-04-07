from core.database import db

class AuthService:

    def login(self, username: str, password: str):
        username_clean = username.lower().strip()
        user = db.authenticate_user(username_clean, password)
        
        if user:
            print(f"✅ Login correcto: {user['username']} (Tier {user['tier']})")
            return (user["username"], user["tier"])
        
        print("❌ Usuario o contraseña incorrectos")
        return None