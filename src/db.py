from __future__ import annotations

from contextlib import asynccontextmanager
from pathlib import Path
from typing import AsyncIterator

import aiosqlite

from db.schema import CREATE_SQL

PROJECT_ROOT = Path(__file__).resolve().parents[1]
DB_PATH = PROJECT_ROOT / "data" / "app.db"


@asynccontextmanager
async def get_db() -> AsyncIterator[aiosqlite.Connection]:
    db = await aiosqlite.connect(DB_PATH)
    db.row_factory = aiosqlite.Row
    try:
        await db.execute("PRAGMA journal_mode=WAL;")
        await db.execute("PRAGMA foreign_keys=ON;")
        await db.executescript(CREATE_SQL)
        await _ensure_legacy_columns(db)
        yield db
        await db.commit()
    except Exception:
        await db.rollback()
        raise
    finally:
        await db.close()


async def _ensure_legacy_columns(db: aiosqlite.Connection) -> None:
    users_columns = await _get_columns(db, "users")
    if "current_ride_id" not in users_columns:
        await db.execute("ALTER TABLE users ADD COLUMN current_ride_id TEXT")


async def _get_columns(db: aiosqlite.Connection, table_name: str) -> set[str]:
    cursor = await db.execute(f"PRAGMA table_info({table_name})")
    rows = await cursor.fetchall()
    await cursor.close()
    return {row["name"] for row in rows}
