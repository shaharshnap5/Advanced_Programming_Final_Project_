from __future__ import annotations

import aiosqlite


class UsersRepository:
    async def get_by_id(self, db: aiosqlite.Connection, user_id: str) -> dict | None:
        cursor = await db.execute(
            """
            SELECT user_id, payment_token, current_ride_id
            FROM users
            WHERE user_id = ?
            """,
            (user_id,),
        )
        row = await cursor.fetchone()
        await cursor.close()
        return dict(row) if row else None

    async def create(
        self,
        db: aiosqlite.Connection,
        user_id: str,
        payment_token: str,
        current_ride_id: str | None = None,
    ) -> bool:
        cursor = await db.execute(
            """
            INSERT OR IGNORE INTO users (user_id, payment_token, current_ride_id)
            VALUES (?, ?, ?)
            """,
            (user_id, payment_token, current_ride_id),
        )
        await db.commit()
        affected = cursor.rowcount
        await cursor.close()
        return affected > 0
