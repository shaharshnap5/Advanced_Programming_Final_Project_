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
