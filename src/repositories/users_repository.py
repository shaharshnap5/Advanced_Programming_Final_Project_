from __future__ import annotations

import aiosqlite
from src.models.user import User


class UsersRepository:
    async def get_by_id(self, db: aiosqlite.Connection, user_id: str) -> User | None:
        cursor = await db.execute(
            """
            SELECT user_id, first_name, last_name, email, payment_token
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
        first_name: str,
        last_name: str,
        email: str,
        payment_token: str,
    ) -> bool:
        cursor = await db.execute(
            """
            INSERT OR IGNORE INTO users (user_id, first_name, last_name, email, payment_token)
            VALUES (?, ?, ?, ?, ?)
            """,
            (user_id, first_name, last_name, email, payment_token),
        )
        await db.commit()
        affected = cursor.rowcount
        await cursor.close()
        return affected > 0

    async def update_current_ride_id(
        self, db: aiosqlite.Connection, user_id: str, ride_id: str | None
    ) -> bool:
        """Update or clear the user's current active ride."""
        cursor = await db.execute(
            """
            UPDATE users
            SET current_ride_id = ?
            WHERE user_id = ?
            """,
            (ride_id, user_id),
        )
        await db.commit()
        affected = cursor.rowcount
        await cursor.close()
        return affected > 0

    async def clear_current_ride(self, db: aiosqlite.Connection, user_id: str) -> bool:
        """Clear the user's current active ride (set to NULL)."""
        return await self.update_current_ride_id(db, user_id, None)

    async def list_active_users(self, db: aiosqlite.Connection) -> list[str]:
        """Return list of user_ids that have active rides (current_ride_id IS NOT NULL)."""
        cursor = await db.execute(
            """
            SELECT user_id FROM users
            WHERE current_ride_id IS NOT NULL
            """
        )
        rows = await cursor.fetchall()
        await cursor.close()
        return [row[0] for row in rows]
