import aiosqlite
from datetime import datetime
from src.models.ride import Ride

class RidesRepository:
    @staticmethod
    def _row_to_ride(row: aiosqlite.Row) -> Ride:
        return Ride(
            ride_id=row["ride_id"],
            user_id=row["user_id"],
            vehicle_id=row["vehicle_id"],
            start_station_id=row["start_station_id"],
            end_station_id=row["end_station_id"],
            start_time=datetime.fromisoformat(row["start_time"]) if isinstance(row["start_time"], str) else row["start_time"],
            end_time=datetime.fromisoformat(row["end_time"]) if (row["end_time"] and isinstance(row["end_time"], str)) else row["end_time"],
            is_degraded_report=bool(row["is_degraded_report"]),
        )

    async def get_by_id(self, db: aiosqlite.Connection, ride_id: str) -> Ride | None:
        """Fetches a ride by ID, or None if not found."""
        cursor = await db.execute(
            "SELECT * FROM rides WHERE ride_id = ?",
            (ride_id,))
        row = await cursor.fetchone()
        await cursor.close()
        if row is None:
            return None
        return self._row_to_ride(row)

    async def get_active_ride_by_user(self, db: aiosqlite.Connection, user_id: str) -> Ride | None:
        """Fetches the active ride for a user as a Ride object, or None if no active ride exists."""
        cursor = await db.execute(
            "SELECT * FROM rides WHERE user_id = ? AND end_time IS NULL",
            (user_id,)
        )
        row = await cursor.fetchone()
        await cursor.close()
        if row is None:
            return None
        return self._row_to_ride(row)

    async def create_active_ride(
        self,
        db: aiosqlite.Connection,
        ride_id: str,
        user_id: str,
        vehicle_id: str,
        start_station_id: int,
        start_time: datetime | None = None
    ):
        """Inserts a new active ride into the database."""
        if start_time is None:
            start_time = datetime.now()

        await db.execute(
            """
            INSERT INTO rides (ride_id, user_id, vehicle_id, start_station_id, is_degraded_report, start_time) 
            VALUES (?, ?, ?, ?, FALSE, ?)
            """,
            (ride_id, user_id, vehicle_id, start_station_id, start_time)
        )

    async def complete_ride(
        self,
        db: aiosqlite.Connection,
        ride_id: str,
        end_station_id: int,
        end_time: datetime | None = None,
        is_degraded_report: bool = False,
    ) -> bool:
        """Mark an active ride as completed and persist its final state."""
        if end_time is None:
            end_time = datetime.now()

        cursor = await db.execute(
            """
            UPDATE rides
            SET end_station_id = ?,
                end_time = ?,
                is_degraded_report = ?
            WHERE ride_id = ?
            """,
            (end_station_id, end_time, int(is_degraded_report), ride_id),
        )
        affected = cursor.rowcount
        await cursor.close()
        return affected > 0