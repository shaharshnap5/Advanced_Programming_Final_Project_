from __future__ import annotations

import uuid

import aiosqlite

from src.exceptions import ConflictException, NotFoundException, ValidationException
from src.repositories.rides_repository import RidesRepository
from src.repositories.stations_repository import StationsRepository
from src.repositories.users_repository import UsersRepository
from src.repositories.vehicles_repository import VehiclesRepository


class RidesService:
    def __init__(
        self,
        rides_repo: RidesRepository | None = None,
        users_repo: UsersRepository | None = None,
        vehicles_repo: VehiclesRepository | None = None,
        stations_repo: StationsRepository | None = None,
    ) -> None:
        self._rides_repo = rides_repo or RidesRepository()
        self._users_repo = users_repo or UsersRepository()
        self._vehicles_repo = vehicles_repo or VehiclesRepository()
        self._stations_repo = stations_repo or StationsRepository()

    async def start_ride(self, db: aiosqlite.Connection, user_id: str, lat: float, lon: float) -> dict:
        user = await self._users_repo.get_by_id(db, user_id)
        if not user:
            raise NotFoundException(f"User {user_id} not found")
        if user["current_ride_id"]:
            raise ConflictException(f"User {user_id} already has an active ride")

        nearest_station = await self._stations_repo.get_nearest(db, lon=lon, lat=lat)
        if not nearest_station:
            raise NotFoundException("No stations found")

        vehicles = await self._vehicles_repo.list_by_station(db, nearest_station["station_id"])
        available_vehicle = next(
            (
                vehicle
                for vehicle in vehicles
                if vehicle["status"] == "available" and vehicle["rides_since_last_treated"] <= 10
            ),
            None,
        )
        if not available_vehicle:
            raise ValidationException(f"No available vehicles at station {nearest_station['station_id']}")

        ride_id = f"RIDE-{uuid.uuid4().hex[:8].upper()}"
        vehicle_id = available_vehicle["vehicle_id"]

        await self._rides_repo.create_ride(
            db,
            ride_id=ride_id,
            user_id=user_id,
            vehicle_id=vehicle_id,
            start_station_id=nearest_station["station_id"],
        )
        await db.execute(
            "UPDATE users SET current_ride_id = ? WHERE user_id = ?",
            (ride_id, user_id),
        )
        await db.execute(
            "UPDATE vehicles SET status = 'rented', station_id = NULL WHERE vehicle_id = ?",
            (vehicle_id,),
        )

        return {
            "ride_id": ride_id,
            "user_id": user_id,
            "vehicle_id": vehicle_id,
            "vehicle_type": available_vehicle["vehicle_type"],
            "start_station_id": nearest_station["station_id"],
        }

    async def end_ride(self, db: aiosqlite.Connection, ride_id: str, lat: float, lon: float) -> dict:
        active_ride = await self._rides_repo.get_active_ride_by_id(db, ride_id)
        if not active_ride:
            raise NotFoundException(f"Ride {ride_id} not found")

        destination_station = await self._stations_repo.get_nearest(db, lon=lon, lat=lat)
        if not destination_station:
            raise NotFoundException("No stations found")

        destination_count = len(destination_station["vehicles"])
        if destination_count >= destination_station["max_capacity"]:
            raise ValidationException(f"Station {destination_station['station_id']} is full")

        vehicle = await self._vehicles_repo.get_by_id(db, active_ride["vehicle_id"])
        if not vehicle:
            raise NotFoundException(f"Vehicle {active_ride['vehicle_id']} not found")

        new_rides_count = vehicle["rides_since_last_treated"] + 1
        new_status = "degraded" if new_rides_count > 10 else "available"
        cost = 15

        await db.execute(
            """
            UPDATE vehicles
            SET status = ?,
                station_id = ?,
                rides_since_last_treated = ?
            WHERE vehicle_id = ?
            """,
            (new_status, destination_station["station_id"], new_rides_count, active_ride["vehicle_id"]),
        )
        await self._rides_repo.end_ride(db, ride_id, destination_station["station_id"], cost)
        await db.execute(
            "UPDATE users SET current_ride_id = NULL WHERE user_id = ?",
            (active_ride["user_id"],),
        )

        return {
            "ride_id": ride_id,
            "end_station_id": destination_station["station_id"],
            "payment_charged": cost,
        }

    async def get_active_users(self, db: aiosqlite.Connection) -> list[str]:
        return await self._rides_repo.get_all_active_users(db)
