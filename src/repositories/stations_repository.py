from __future__ import annotations

import aiosqlite


class StationsRepository:
    async def get_by_id(self, db: aiosqlite.Connection, station_id: int) -> dict | None:
        cursor = await db.execute(
            """
            SELECT station_id, name, lat, lon, max_capacity
            FROM stations
            WHERE station_id = ?
            """,
            (station_id,),
        )
        row = await cursor.fetchone()
        await cursor.close()
        return dict(row) if row else None

    async def get_nearest(self, db: aiosqlite.Connection, lon: float, lat: float) -> dict | None:
        cursor = await db.execute(
            """
            SELECT
                station_id,
                name,
                lat,
                lon,
                max_capacity,
                ((lat - ?) * (lat - ?) + (lon - ?) * (lon - ?)) AS distance
            FROM stations
            ORDER BY distance ASC
            LIMIT 1
            """,
            (lat, lat, lon, lon),
        )
        row = await cursor.fetchone()
        await cursor.close()
        return dict(row) if row else None
