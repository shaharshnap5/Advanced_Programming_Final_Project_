from __future__ import annotations

import aiosqlite

from src.repositories.stations_repository import StationsRepository
from src.models.station import Station


class StationsService:
    def __init__(self, repository: StationsRepository | None = None) -> None:
        self._repository = repository or StationsRepository()

    async def get_station_by_id(self, db: aiosqlite.Connection, station_id: int) -> Station | None:
        data = await self._repository.get_by_id(db, station_id)
        return Station.model_validate(data) if data else None

    async def get_nearest_station(self, db: aiosqlite.Connection, lon: float, lat: float) -> Station | None:
        data = await self._repository.get_nearest(db, lon=lon, lat=lat)
        return Station.model_validate(data) if data else None

    async def get_nearest_station_with_capacity(
        self, db: aiosqlite.Connection, lon: float, lat: float
    ) -> Station | None:
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

        # Convert to Station model (ignore current_capacity)
        return Station.model_validate({
            "station_id": nearest["station_id"],
            "name": nearest.get("name"),
            "lat": nearest["lat"],
            "lon": nearest["lon"],
            "max_capacity": nearest["max_capacity"],
            "vehicles": [],
        })
