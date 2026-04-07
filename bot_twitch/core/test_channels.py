# test_channels.py
from database import DatabaseManager

db = DatabaseManager()

# --- PROBAR CANALES ---
print("=== CANALES ===")
db.set_channel_tier("123456", "fantan_channel", "premium")
print("Tier del canal 123456:", db.get_channel_tier("123456"))

db.set_channel_tier("123456", "fantan_channel", "gold")
print("Tier actualizado del canal 123456:", db.get_channel_tier("123456"))

# --- PROBAR MÓDULOS ---
print("\n=== MÓDULOS ===")
db.set_module("123456", "iracing", True)
db.set_module("123456", "games", False)

print("Iracing habilitado:", db.is_module_enabled("123456", "iracing"))
print("Games habilitado:", db.is_module_enabled("123456", "games"))

# --- CANAL QUE NO EXISTE ---
print("\n=== CANAL INEXISTENTE ===")
print("Tier canal desconocido:", db.get_channel_tier("999999"))
print("Módulo iracing desconocido:", db.is_module_enabled("999999", "iracing"))