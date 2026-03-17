from __future__ import annotations

import aiosqlite

from src.models.user import User


class UsersRepository:
    async def get_by_id(self, db: aiosqlite.Connection, user_id: str) -> User | None:
        cursor = await db.execute(
            """
            SELECT user_id, payment_token
            FROM users
            WHERE user_id = ?
            """,
            (user_id,),
        )
        row = await cursor.fetchone()
        await cursor.close()
        return User(**dict(row)) if row else None

    async def create(
        self,
        db: aiosqlite.Connection,
        user_id: str,
        payment_token: str,
    ) -> bool:
        cursor = await db.execute(
            """
            INSERT OR IGNORE INTO users (user_id, payment_token)
            VALUES (?, ?)
            """,
            (user_id, payment_token),
        )
        await db.commit()
        affected = cursor.rowcount
        await cursor.close()
        return affected > 0
