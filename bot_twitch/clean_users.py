# clean_users.py
from core.database import db

def clean_users():
    cursor = db._cursor()
    
    users = db.get_all_users()
    print(f"Usuarios actuales: {len(users)}")
    for u in users:
        print(f"  - '{u['username']}' (Tier {u['tier']})")
    
    cursor.execute("DELETE FROM users WHERE tier < 3")
    cursor.execute("DELETE FROM user_config WHERE username != 'admin'")
    db._commit()
    
    users_after = db.get_all_users()
    print(f"\n✅ Limpieza completada. Quedan {len(users_after)} usuarios:")
    for u in users_after:
        print(f"  - '{u['username']}' (Tier {u['tier']})")

if __name__ == "__main__":
    clean_users()