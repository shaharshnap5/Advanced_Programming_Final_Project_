from __future__ import annotations
from src.utilis.distance import calculate_euclidean_distance
import aiosqlite

from src.repositories.stations_repository import StationsRepository
from src.models.station import Station, StationWithDistance




class StationsService:
    def __init__(self, repository: StationsRepository | None = None) -> None:
        self._repository = repository or StationsRepository()

    async def get_station_by_id(self, db: aiosqlite.Connection, station_id: int) -> Station | None:
        return await self._repository.get_by_id(db, station_id)

    async def get_nearest_station(self, db: aiosqlite.Connection, lon: float, lat: float) -> StationWithDistance | None:
        return await self._repository.get_nearest(db, lon=lon, lat=lat)


    # Add this helper function if you don't have it already

    async def get_nearest_station_with_vehicles(self, db, lon: float, lat: float) -> Station | None:
        # 1. Get the raw list from the repository function we just wrote
        active_stations = await self._repository.get_stations_with_available_vehicles(db)

        if not active_stations:
            return None

        # 2. Use Python to find the one with the shortest distance
        nearest_station = min(
            active_stations,
            key=lambda s: calculate_euclidean_distance(lon, lat, s.lon, s.lat)
        )

        return nearest_station
