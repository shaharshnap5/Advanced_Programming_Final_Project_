from __future__ import annotations

import aiosqlite
from src.models.station import Station, StationWithDistance


class StationsRepository:
    async def get_by_id(self, db: aiosqlite.Connection, station_id: int) -> Station | None:
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
        return Station(**dict(row)) if row else None

    async def get_nearest(self, db: aiosqlite.Connection, lon: float, lat: float) -> StationWithDistance | None:
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
        if row:
            row_dict = dict(row)
            return StationWithDistance(**row_dict)
        return None

    async def get_stations_with_available_vehicles(self, db: aiosqlite.Connection) -> list[Station]:
        # The JOIN ensures we only get stations that have at least one 'available' vehicle
        query = """
            SELECT DISTINCT s.station_id, s.name, s.lat, s.lon, s.max_capacity 
            FROM stations s
            JOIN vehicles v ON s.station_id = v.station_id
            WHERE v.status = 'available'
        """
        db.row_factory = aiosqlite.Row
        async with db.execute(query) as cursor:
            rows = await cursor.fetchall()
            return [Station(**dict(row)) for row in rows]

    async def list_with_capacity(self, db: aiosqlite.Connection) -> list[dict]:
        """
        List all stations with their current capacity.
        Returns: list of dicts with station_id, name, lat, lon, max_capacity, current_capacity
        """
        query = """
            SELECT
                s.station_id,
                s.name,
                s.lat,
                s.lon,
                s.max_capacity,
                COALESCE(COUNT(v.vehicle_id), 0) as current_capacity
            FROM stations s
            LEFT JOIN vehicles v ON s.station_id = v.station_id
            GROUP BY s.station_id
        """
        cursor = await db.execute(query)
        rows = await cursor.fetchall()
        await cursor.close()
        return [dict(row) for row in rows]
