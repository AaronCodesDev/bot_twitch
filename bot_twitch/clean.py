# clean.py
from core.database import db

cursor = db._cursor()
cursor.execute("DELETE FROM recuerdos")
cursor.execute("DELETE FROM hechos")
cursor.execute("DELETE FROM user_frases")
cursor.execute("DELETE FROM user_profiles")
cursor.execute("DELETE FROM command_history")
cursor.execute("DELETE FROM ideas")
cursor.execute("DELETE FROM subs_mensuales")
cursor.execute("DELETE FROM sqlite_sequence WHERE name NOT IN ('users', 'modules')")
db._commit()
print("✅ Datos de prueba limpiados")