from __future__ import annotations

import os
from pathlib import Path
from typing import AsyncIterator

import aiosqlite

PROJECT_ROOT = Path(__file__).resolve().parents[1]
DB_PATH = Path(os.getenv("APP_DB_PATH", str(PROJECT_ROOT / "data" / "app.db")))



async def get_db() -> AsyncIterator[aiosqlite.Connection]:
    db = await aiosqlite.connect(DB_PATH)
    db.row_factory = aiosqlite.Row
    try:
        await db.execute("PRAGMA journal_mode=WAL;")
        await db.execute("PRAGMA synchronous=FULL;")
        await db.execute("PRAGMA foreign_keys=ON;")
        yield db
        await db.commit()
    except Exception:
        await db.rollback()
        raise
    finally:
        await db.close()
