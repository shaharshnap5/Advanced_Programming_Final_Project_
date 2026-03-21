from __future__ import annotations

import aiosqlite
from src.models.station import Station, StationWithDistance
from src.models.lock_manager import LockManager


class StationsRepository:
    async def _fetch_vehicles_for_station(
        self, db: aiosqlite.Connection, station_id: int
    ) -> list[str]:
        """Fetch all vehicle IDs docked at a specific station."""
        cursor = await db.execute(
            """
            SELECT vehicle_id
            FROM vehicles
            WHERE station_id = ?
            """,
            (station_id,),
        )
        rows = await cursor.fetchall()
        await cursor.close()
        return [row[0] for row in rows]

    async def get_by_id(
        self, db: aiosqlite.Connection, station_id: int
    ) -> Station | None:
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
        if not row:
            return None

        station_dict = dict(row)
        # Fetch vehicles docked at this station
        vehicles = await self._fetch_vehicles_for_station(db, station_id)
        station_dict["vehicles"] = vehicles
        return Station(**station_dict)

    async def get_nearest(
        self, db: aiosqlite.Connection, lon: float, lat: float
    ) -> StationWithDistance | None:
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
        if not row:
            return None

        row_dict = dict(row)
        station_id = row_dict["station_id"]
        # Fetch vehicles docked at this station
        vehicles = await self._fetch_vehicles_for_station(db, station_id)
        row_dict["vehicles"] = vehicles
        return StationWithDistance(**row_dict)

    async def get_stations_with_available_vehicles(
        self, db: aiosqlite.Connection
    ) -> list[Station]:
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
            stations = []
            for row in rows:
                station_dict = dict(row)
                station_id = station_dict["station_id"]
                # Fetch all vehicles docked at this station
                vehicles = await self._fetch_vehicles_for_station(db, station_id)
                station_dict["vehicles"] = vehicles
                stations.append(Station(**station_dict))
            return stations

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

    async def check_and_reserve_capacity(
        self, db: aiosqlite.Connection, station_id: int
    ) -> bool:
        """
        Atomically check if a station has capacity and reserve a spot.
        Uses locking to prevent race conditions when multiple vehicles try to dock simultaneously.

        Returns: True if capacity is available and reserved, False otherwise
        """
        lock_manager = LockManager()

        async with lock_manager.station_lock(station_id):
            # Get station info and current capacity
            cursor = await db.execute(
                """
                SELECT s.max_capacity, COALESCE(COUNT(v.vehicle_id), 0) as current_capacity
                FROM stations s
                LEFT JOIN vehicles v ON s.station_id = v.station_id
                WHERE s.station_id = ?
                GROUP BY s.station_id
                """,
                (station_id,),
            )
            row = await cursor.fetchone()
            await cursor.close()

            if not row:
                return False

            max_capacity = row["max_capacity"]
            current_capacity = row["current_capacity"]

            # Check if there's space
            return current_capacity < max_capacity
