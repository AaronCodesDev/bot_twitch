"""
Esquema de la base de datos SQLite.
Todas las tablas del modo carrera se definen aquí.
"""

CREATE_TABLES = """
CREATE TABLE IF NOT EXISTS pilot (
    id INTEGER PRIMARY KEY,
    iracing_id TEXT UNIQUE,
    name TEXT,
    balance REAL DEFAULT 0,
    reputation INTEGER DEFAULT 50,
    created_at TEXT DEFAULT (datetime('now'))
);

CREATE TABLE IF NOT EXISTS race_result (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    pilot_id INTEGER,
    subsession_id TEXT UNIQUE,
    track TEXT,
    series TEXT,
    finish_position INTEGER,
    incidents INTEGER,
    irating_change INTEGER,
    sr_change REAL,
    prize_money REAL DEFAULT 0,
    raced_at TEXT,
    FOREIGN KEY (pilot_id) REFERENCES pilot(id)
);

CREATE TABLE IF NOT EXISTS contract (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    pilot_id INTEGER,
    team_name TEXT,
    salary_per_race REAL,
    min_sr REAL,
    min_irating INTEGER,
    min_wins INTEGER,
    max_incidents_per_race INTEGER,
    status TEXT DEFAULT 'active',
    started_at TEXT DEFAULT (datetime('now')),
    ended_at TEXT,
    FOREIGN KEY (pilot_id) REFERENCES pilot(id)
);

CREATE TABLE IF NOT EXISTS sanction (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    pilot_id INTEGER,
    type TEXT,
    reason TEXT,
    days_rest INTEGER DEFAULT 0,
    races_banned INTEGER DEFAULT 0,
    active INTEGER DEFAULT 1,
    created_at TEXT DEFAULT (datetime('now')),
    ends_at TEXT,
    FOREIGN KEY (pilot_id) REFERENCES pilot(id)
);

CREATE TABLE IF NOT EXISTS owned_item (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    pilot_id INTEGER,
    item_id TEXT,
    item_name TEXT,
    price_paid REAL,
    bought_at TEXT DEFAULT (datetime('now')),
    FOREIGN KEY (pilot_id) REFERENCES pilot(id)
);

CREATE TABLE IF NOT EXISTS staff (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    pilot_id INTEGER,
    staff_type TEXT,
    name TEXT,
    monthly_cost REAL,
    benefit_type TEXT,
    benefit_value REAL,
    active INTEGER DEFAULT 1,
    hired_at TEXT DEFAULT (datetime('now')),
    FOREIGN KEY (pilot_id) REFERENCES pilot(id)
);
"""
