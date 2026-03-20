from __future__ import annotations
from src.utilis.distance import calculate_euclidean_distance
import aiosqlite

from src.repositories.stations_repository import StationsRepository
from src.repositories.vehicles_repository import VehiclesRepository
from src.models.station import Station, StationWithDistance




class StationsService:
    def __init__(
        self,
        repository: StationsRepository | None = None,
        vehicles_repository: VehiclesRepository | None = None,
    ) -> None:
        self._repository = repository or StationsRepository()
        self._vehicles_repository = vehicles_repository or VehiclesRepository()

    async def get_station_by_id(self, db: aiosqlite.Connection, station_id: int) -> Station | None:
        return await self._repository.get_by_id(db, station_id)

    async def get_nearest_station(self, db: aiosqlite.Connection, lon: float, lat: float) -> StationWithDistance | None:
        station = await self._repository.get_nearest(db, lon=lon, lat=lat)
        if not station:
            return None

        if isinstance(station, dict):
            station = StationWithDistance(**station)

        available_vehicles = await self._vehicles_repository.get_available_vehicles_by_station(db, station.station_id)
        type_priority = {
            "scooter": 1,
            "electric_bicycle": 2,
            "bicycle": 3,
        }

        if available_vehicles:
            best_vehicle = sorted(
                available_vehicles,
                key=lambda v: (type_priority.get(v.vehicle_type.value, 4), v.vehicle_id),
            )[0]
            station.nearest_available_vehicle = best_vehicle

        return station


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

    async def get_stations_with_capacity(self, db: aiosqlite.Connection) -> list[dict]:
        """Return list of stations with their current capacity info."""
        return await self._repository.list_with_capacity(db)
