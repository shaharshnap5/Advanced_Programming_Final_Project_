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