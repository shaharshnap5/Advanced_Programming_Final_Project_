from __future__ import annotations

import aiosqlite

from src.repositories.stations_repository import StationsRepository


class StationsService:
    def __init__(self, repository: StationsRepository | None = None) -> None:
        self._repository = repository or StationsRepository()

    async def get_station_by_id(self, db: aiosqlite.Connection, station_id: int) -> dict | None:
        return await self._repository.get_by_id(db, station_id)

    async def get_nearest_station(self, db: aiosqlite.Connection, lon: float, lat: float) -> dict | None:
        return await self._repository.get_nearest(db, lon=lon, lat=lat)

    async def get_nearest_station_with_capacity(self, db: aiosqlite.Connection, lon: float, lat: float) -> dict | None:
        """Returns the nearest station that has at least one empty slot."""
        stations = await self._repository.list_with_capacity(db)
        # Filter only stations with free capacity
        available = [s for s in stations if s["current_capacity"] < s["max_capacity"]]
        if not available:
            return None

        # Use euclidean distance helper for consistency
        from src.utils.distance import euclidean_distance

        nearest = min(
            available,
            key=lambda s: euclidean_distance(lat, lon, s["lat"], s["lon"]),
        )
        return nearest
