from __future__ import annotations
from src.models.vehicle import Vehicle, VehicleStatus, VehicleFactory

import aiosqlite
from src.models.lock_manager import LockManager


class VehiclesRepository:
    BASE_SELECT = """
        SELECT
            v.vehicle_id,
            v.station_id,
            v.vehicle_type,
            v.status,
            v.rides_since_last_treated,
            v.last_treated_date,
            CASE
                WHEN v.vehicle_type = 'electric_bicycle' THEN e.battery
                WHEN v.vehicle_type = 'scooter' THEN s.battery
                ELSE NULL
            END AS battery
        FROM vehicles v
        LEFT JOIN ebikes e ON v.vehicle_id = e.vehicle_id
        LEFT JOIN scooters s ON v.vehicle_id = s.vehicle_id
    """

    @staticmethod
    def _to_vehicle(row: aiosqlite.Row) -> Vehicle:
        return VehicleFactory.from_row(dict(row))

    async def _update_electric_battery(self, db: aiosqlite.Connection, vehicle: Vehicle) -> None:
        if vehicle.vehicle_type.value == "electric_bicycle":
            await db.execute(
                "UPDATE ebikes SET battery = ? WHERE vehicle_id = ?",
                (vehicle.battery, vehicle.vehicle_id),
            )
        elif vehicle.vehicle_type.value == "scooter":
            await db.execute(
                "UPDATE scooters SET battery = ? WHERE vehicle_id = ?",
                (vehicle.battery, vehicle.vehicle_id),
            )

    async def get_by_id(self, db: aiosqlite.Connection, vehicle_id: str) -> Vehicle | None:
        cursor = await db.execute(
            f"""
            {self.BASE_SELECT}
            WHERE v.vehicle_id = ?
            """,
            (vehicle_id,),
        )
        row = await cursor.fetchone()
        await cursor.close()
        return self._to_vehicle(row) if row else None

    async def list_all(self, db: aiosqlite.Connection) -> list[Vehicle]:
        cursor = await db.execute(
            self.BASE_SELECT
        )
        rows = await cursor.fetchall()
        await cursor.close()
        return [self._to_vehicle(row) for row in rows]

    async def list_by_station(self, db: aiosqlite.Connection, station_id: int) -> list[Vehicle]:
        cursor = await db.execute(
            f"""
            {self.BASE_SELECT}
            WHERE v.station_id = ?
            """,
            (station_id,),
        )
        rows = await cursor.fetchall()
        await cursor.close()
        return [self._to_vehicle(row) for row in rows]

    async def list_vehicles_eligible_for_treatment(self, db: aiosqlite.Connection) -> list[Vehicle]:
        """List vehicles eligible for treatment: degraded OR rides >= 7."""
        cursor = await db.execute(
            f"""
            {self.BASE_SELECT}
            WHERE v.status = 'degraded' OR v.rides_since_last_treated >= 7
            """
        )
        rows = await cursor.fetchall()
        await cursor.close()
        return [self._to_vehicle(row) for row in rows]

    async def treat_vehicle(self, db: aiosqlite.Connection, vehicle_id: str, station_id: int | None = None) -> bool:
        """Perform maintenance on a vehicle.
        Sets: status='available', rides_since_last_treated=0, last_treated_date=today.
        Updates station_id if provided by service layer.
        """
        vehicle = await self.get_by_id(db, vehicle_id)
        if not vehicle:
            return False

        # Service layer determines whether to update station_id
        if station_id is not None:
            vehicle.station_id = station_id

        vehicle.treat()

        cursor = await db.execute(
            """
            UPDATE vehicles
            SET status = ?,
                rides_since_last_treated = ?,
                last_treated_date = ?,
                station_id = ?
            WHERE vehicle_id = ?
            """,
            (
                vehicle.status.value,
                vehicle.rides_since_last_treated,
                vehicle.last_treated_date.isoformat() if vehicle.last_treated_date else None,
                vehicle.station_id,
                vehicle_id,
            ),
        )
        await self._update_electric_battery(db, vehicle)
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

    async def get_available_vehicle(self, db: aiosqlite.Connection, station_id: int) -> Vehicle | None:
        """Finds one available vehicle at the given station."""
        cursor = await db.execute(
            f"""
            {self.BASE_SELECT}
            WHERE v.station_id = ? AND v.status = 'available' 
            LIMIT 1
            """,
            (station_id,)
        )
        row = await cursor.fetchone()
        await cursor.close()
        return self._to_vehicle(row) if row else None

    async def mark_vehicle_as_rented(self, db: aiosqlite.Connection, vehicle_id: str) -> Vehicle | None:
        """Rents a vehicle through its domain model and persists the state with locking."""
        lock_manager = LockManager()

        async with lock_manager.vehicle_lock(vehicle_id):
            vehicle = await self.get_by_id(db, vehicle_id)
            if not vehicle:
                return None

            # Check if vehicle is available before renting
            if vehicle.status != VehicleStatus.available:
                raise ValueError(f"Vehicle {vehicle_id} is not available for rental")

            vehicle.rent()

            await db.execute(
                """
                UPDATE vehicles
                SET status = ?, station_id = ?
                WHERE vehicle_id = ?
                """,
                (vehicle.status.value, vehicle.station_id, vehicle_id),
            )
            await db.commit()
            return vehicle

    async def get_available_vehicles_by_station(self, db: aiosqlite.Connection, station_id: int) -> list[Vehicle]:
        query = f"""
            {self.BASE_SELECT}
            WHERE v.station_id = ? AND v.status = 'available'
        """
        db.row_factory = aiosqlite.Row
        async with db.execute(query, (station_id,)) as cursor:
            rows = await cursor.fetchall()
            return [self._to_vehicle(row) for row in rows]

    async def dock_vehicle(self, db: aiosqlite.Connection, vehicle_id: str, station_id: int) -> Vehicle | None:
        """
        Docks a vehicle at a station after ride completion with locking.
        The domain model determines ride counters, battery drain, and final status.
        """
        lock_manager = LockManager()

        async with lock_manager.vehicle_lock(vehicle_id):
            vehicle = await self.get_by_id(db, vehicle_id)
            if not vehicle:
                raise ValueError(f"Vehicle {vehicle_id} not found")

            if vehicle.status not in [VehicleStatus.rented, VehicleStatus.available]:
                raise ValueError(f"Vehicle {vehicle_id} cannot be docked in status {vehicle.status}")

            vehicle.return_vehicle(station_id)

            cursor = await db.execute(
                """
                UPDATE vehicles
                SET station_id = ?,
                    rides_since_last_treated = ?,
                    status = ?
                WHERE vehicle_id = ?
                """,
                (
                    vehicle.station_id,
                    vehicle.rides_since_last_treated,
                    vehicle.status.value,
                    vehicle_id,
                ),
            )
            await self._update_electric_battery(db, vehicle)
            await db.commit()
            affected = cursor.rowcount
            await cursor.close()

            if affected > 0:
                return await self.get_by_id(db, vehicle_id)
            return None
