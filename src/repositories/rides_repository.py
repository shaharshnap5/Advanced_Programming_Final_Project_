from __future__ import annotations

import aiosqlite


class RidesRepository:
    async def create_ride(
        self,
        db: aiosqlite.Connection,
        ride_id: str,
        user_id: str,
        vehicle_id: str,
        start_station_id: int,
    ) -> None:
        await db.execute(
            """
            INSERT INTO rides (
                ride_id,
                user_id,
                vehicle_id,
                start_station_id,
                start_time,
                status
            )
            VALUES (?, ?, ?, ?, datetime('now'), 'active')
            """,
            (ride_id, user_id, vehicle_id, start_station_id),
        )

    async def get_active_ride_by_user(self, db: aiosqlite.Connection, user_id: str) -> dict | None:
        cursor = await db.execute(
            """
            SELECT ride_id, user_id, vehicle_id, start_station_id
            FROM rides
            WHERE user_id = ? AND status = 'active'
            ORDER BY start_time DESC
            LIMIT 1
            """,
            (user_id,),
        )
        row = await cursor.fetchone()
        await cursor.close()
        return dict(row) if row else None

    async def get_active_ride_by_id(self, db: aiosqlite.Connection, ride_id: str) -> dict | None:
        cursor = await db.execute(
            """
            SELECT ride_id, user_id, vehicle_id, start_station_id
            FROM rides
            WHERE ride_id = ? AND status = 'active'
            """,
            (ride_id,),
        )
        row = await cursor.fetchone()
        await cursor.close()
        return dict(row) if row else None

    async def end_ride(
        self,
        db: aiosqlite.Connection,
        ride_id: str,
        end_station_id: int,
        cost: int,
    ) -> None:
        await db.execute(
            """
            UPDATE rides
            SET end_station_id = ?,
                end_time = datetime('now'),
                cost = ?,
                status = 'completed'
            WHERE ride_id = ?
            """,
            (end_station_id, cost, ride_id),
        )

    async def get_all_active_users(self, db: aiosqlite.Connection) -> list[str]:
        cursor = await db.execute(
            """
            SELECT user_id
            FROM users
            WHERE current_ride_id IS NOT NULL
            ORDER BY user_id
            """
        )
        rows = await cursor.fetchall()
        await cursor.close()
        return [row["user_id"] for row in rows]
