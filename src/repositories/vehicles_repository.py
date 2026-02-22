from __future__ import annotations

import aiosqlite


class VehiclesRepository:
    async def get_by_id(self, db: aiosqlite.Connection, vehicle_id: str) -> dict | None:
        cursor = await db.execute(
            """
            SELECT
                vehicle_id,
                station_id,
                vehicle_type,
                status,
                rides_since_last_treated,
                last_treated_date
            FROM vehicles
            WHERE vehicle_id = ?
            """,
            (vehicle_id,),
        )
        row = await cursor.fetchone()
        await cursor.close()
        return dict(row) if row else None

    async def list_all(self, db: aiosqlite.Connection) -> list[dict]:
        cursor = await db.execute(
            """
            SELECT
                vehicle_id,
                station_id,
                vehicle_type,
                status,
                rides_since_last_treated,
                last_treated_date
            FROM vehicles
            """
        )
        rows = await cursor.fetchall()
        await cursor.close()
        return [dict(row) for row in rows]

    async def list_by_station(self, db: aiosqlite.Connection, station_id: int) -> list[dict]:
        cursor = await db.execute(
            """
            SELECT
                vehicle_id,
                station_id,
                vehicle_type,
                status,
                rides_since_last_treated,
                last_treated_date
            FROM vehicles
            WHERE station_id = ?
            """,
            (station_id,),
        )
        rows = await cursor.fetchall()
        await cursor.close()
        return [dict(row) for row in rows]
