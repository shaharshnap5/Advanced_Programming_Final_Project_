import aiosqlite
from datetime import datetime

class RidesRepository:
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
        await db.commit()

    async def get_active_user_ids(self, db: aiosqlite.Connection) -> list[str]:
        """Returns the list of user IDs with currently active rides."""
        cursor = await db.execute(
            """
            SELECT DISTINCT user_id
            FROM rides
            WHERE end_time IS NULL OR end_station_id IS NULL
            """
        )
        rows = await cursor.fetchall()
        await cursor.close()
        return [row["user_id"] for row in rows if row["user_id"] is not None]
