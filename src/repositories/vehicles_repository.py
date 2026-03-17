from __future__ import annotations
from src.models.vehicle import Vehicle

import aiosqlite


class VehiclesRepository:
    async def get_by_id(self, db: aiosqlite.Connection, vehicle_id: str) -> Vehicle | None:
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
        return Vehicle(**dict(row)) if row else None

    async def list_all(self, db: aiosqlite.Connection) -> list[Vehicle]:
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
        return [Vehicle(**dict(row)) for row in rows]

    async def list_by_station(self, db: aiosqlite.Connection, station_id: int) -> list[Vehicle]:
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
        return [Vehicle(**dict(row)) for row in rows]

    async def list_vehicles_eligible_for_treatment(self, db: aiosqlite.Connection) -> list[Vehicle]:
        """List vehicles eligible for treatment: degraded OR rides >= 7."""
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
            WHERE status = 'degraded' OR rides_since_last_treated >= 7
            """
        )
        rows = await cursor.fetchall()
        await cursor.close()
        return [Vehicle(**dict(row)) for row in rows]

    async def treat_vehicle(self, db: aiosqlite.Connection, vehicle_id: str, station_id: int | None = None) -> bool:
        """Perform maintenance on a vehicle.
        Sets: status='available', rides_since_last_treated=0, last_treated_date=today.
        For previously degraded vehicles, assigns a station.
        """
        import datetime
        cursor = await db.execute(
            """
            UPDATE vehicles
            SET status = 'available',
                rides_since_last_treated = 0,
                last_treated_date = ?,
                station_id = CASE WHEN station_id IS NULL AND ? IS NOT NULL THEN ? ELSE station_id END
            WHERE vehicle_id = ?
            """,
            (datetime.date.today().isoformat(), station_id, station_id, vehicle_id),
        )
        await db.commit()
        affected = cursor.rowcount
        await cursor.close()
        return affected > 0

    async def update_vehicle_status(self, db: aiosqlite.Connection, vehicle_id: str, status: str) -> bool:
        """Set the status field for a given vehicle."""
        cursor = await db.execute(
            """
            UPDATE vehicles
            SET status = ?
            WHERE vehicle_id = ?
            """,
            (status, vehicle_id),
        )
        await db.commit()
        affected = cursor.rowcount
        await cursor.close()
        return affected > 0

    async def get_available_vehicle(self, db: aiosqlite.Connection, station_id: int) -> list[Vehicle] | None:
        """Finds one available vehicle at the given station."""
        cursor = await db.execute(
            """
            SELECT vehicle_id, vehicle_type 
            FROM vehicles 
            WHERE station_id = ? AND status = 'available' 
            LIMIT 1
            """,
            (station_id,)
        )
        row = await cursor.fetchone()
        return Vehicle(**dict(row)) if row else None

    async def mark_vehicle_as_rented(self, db: aiosqlite.Connection, vehicle_id: str):
        """Updates the vehicle status to rented and removes it from the station."""
        await db.execute(
            """
            UPDATE vehicles 
            SET status = 'rented', station_id = NULL 
            WHERE vehicle_id = ?
            """,
            (vehicle_id,)
        )
        # We commit right away to ensure state is safely persisted to the disk!
        await db.commit()

    async def get_available_vehicles_by_station(self, db: aiosqlite.Connection, station_id: int) -> list[Vehicle]:
        query = """
            SELECT * FROM vehicles 
            WHERE station_id = ? AND status = 'available'
        """
        db.row_factory = aiosqlite.Row
        async with db.execute(query, (station_id,)) as cursor:
            rows = await cursor.fetchall()
            return [Vehicle(**dict(row)) for row in rows]