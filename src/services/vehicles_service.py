from __future__ import annotations

import aiosqlite

from src.repositories.vehicles_repository import VehiclesRepository


class VehiclesService:
    def __init__(self, repository: VehiclesRepository | None = None) -> None:
        self._repository = repository or VehiclesRepository()

    async def get_vehicle_by_id(self, db: aiosqlite.Connection, vehicle_id: str) -> dict | None:
        return await self._repository.get_by_id(db, vehicle_id)

    async def list_vehicles(self, db: aiosqlite.Connection) -> list[dict]:
        return await self._repository.list_all(db)

    async def list_vehicles_by_station(self, db: aiosqlite.Connection, station_id: int) -> list[dict]:
        return await self._repository.list_by_station(db, station_id)
