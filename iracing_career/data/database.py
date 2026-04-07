import os
import aiosqlite
from contextlib import asynccontextmanager
from data.models import CREATE_TABLES

DB_PATH = os.getenv("DB_PATH", "data/career.db")


@asynccontextmanager
async def get_db():
    """Abre conexión SQLite y la cierra automáticamente."""
    os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)

    db = await aiosqlite.connect(DB_PATH)
    db.row_factory = aiosqlite.Row

    try:
        yield db
    finally:
        await db.close()


async def init_db():
    """Crea las tablas si no existen."""
    async with get_db() as db:
        await db.executescript(CREATE_TABLES)
        await db.commit()