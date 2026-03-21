from __future__ import annotations

import aiosqlite


class StationsRepository:
    async def get_by_id(self, db: aiosqlite.Connection, station_id: int) -> dict | None:
        cursor = await db.execute(
            """
            SELECT
                s.station_id,
                s.name,
                s.lat,
                s.lon,
                s.max_capacity,
                COALESCE(GROUP_CONCAT(v.vehicle_id), '') AS vehicles
            FROM stations
            AS s
            LEFT JOIN vehicles AS v ON v.station_id = s.station_id
            WHERE s.station_id = ?
            GROUP BY s.station_id, s.name, s.lat, s.lon, s.max_capacity
            """,
            (station_id,),
        )
        row = await cursor.fetchone()
        await cursor.close()
        return _row_to_station(row)

    async def get_nearest(self, db: aiosqlite.Connection, lon: float, lat: float) -> dict | None:
        cursor = await db.execute(
            """
            SELECT
                s.station_id,
                s.name,
                s.lat,
                s.lon,
                s.max_capacity,
                COALESCE(GROUP_CONCAT(v.vehicle_id), '') AS vehicles,
                ((s.lat - ?) * (s.lat - ?) + (s.lon - ?) * (s.lon - ?)) AS distance
            FROM stations AS s
            LEFT JOIN vehicles AS v ON v.station_id = s.station_id
            GROUP BY s.station_id, s.name, s.lat, s.lon, s.max_capacity
            ORDER BY distance ASC
            LIMIT 1
            """,
            (lat, lat, lon, lon),
        )
        row = await cursor.fetchone()
        await cursor.close()
        return _row_to_station(row)


def _row_to_station(row: aiosqlite.Row | None) -> dict | None:
    if not row:
        return None

    station = dict(row)
    vehicles = station.get("vehicles", "")
    station["vehicles"] = [vehicle_id for vehicle_id in vehicles.split(",") if vehicle_id]
    return station
