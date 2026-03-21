import uuid
import aiosqlite
from fastapi import HTTPException
from datetime import datetime

from src.models.ride import Ride
from src.models.user import User
from src.models.vehicle import VehicleStatus, VehicleType
from src.services.stations_service import StationsService
from src.repositories.vehicles_repository import VehiclesRepository
from src.repositories.rides_repository import RidesRepository
from src.repositories.users_repository import UsersRepository
from src.utilis.distance import calculate_euclidean_distance


class RideService:
    def __init__(self):
        self.vehicles_repo = VehiclesRepository()
        self.rides_repo = RidesRepository()
        self.stations_service = StationsService()
        self.users_repo = UsersRepository()

    @staticmethod
    def _ensure(condition: bool, status_code: int, detail: str) -> None:
        if not condition:
            raise HTTPException(status_code=status_code, detail=detail)

    async def _pick_vehicle_by_location(
        self,
        db: aiosqlite.Connection,
        lon: float | None,
        lat: float | None,
    ) -> tuple:
        self._ensure(
            lon is not None and lat is not None, 400, "Both lon and lat are required."
        )

        nearest_station = await self.stations_service.get_nearest_station_with_vehicles(
            db, lon=lon, lat=lat
        )
        self._ensure(
            nearest_station is not None,
            404,
            "No available vehicles found in the entire system.",
        )

        station_id = nearest_station.station_id
        available_vehicles = await self.vehicles_repo.get_available_vehicles_by_station(
            db, station_id
        )

        type_priority = {
            VehicleType.scooter: 1,
            VehicleType.electric_bicycle: 2,
            VehicleType.bicycle: 3,
        }

        sorted_vehicles = sorted(
            available_vehicles,
            key=lambda v: (type_priority.get(v.vehicle_type, 4), v.vehicle_id),
        )

        picked_vehicle = next(
            (vehicle for vehicle in sorted_vehicles if vehicle.can_rent()), None
        )
        self._ensure(
            picked_vehicle is not None,
            409,
            "No available vehicles have sufficient charge/eligibility.",
        )
        self._ensure(
            picked_vehicle.status == VehicleStatus.available,
            409,
            "Vehicle is not available.",
        )

        return picked_vehicle, station_id

    async def list_active_users(self, db: aiosqlite.Connection) -> list[User]:
        """Return User objects currently in active rides."""
        return await self.rides_repo.get_active_users(db)

    async def start_new_ride(
        self,
        db: aiosqlite.Connection,
        user_id: str,
        lon: float | None = None,
        lat: float | None = None,
    ) -> Ride:
        try:
            user = await self.users_repo.get_by_id(db, user_id)
            self._ensure(user is not None, 404, f"User {user_id} not found.")

            active_ride = await self.rides_repo.get_active_ride_by_user(db, user_id)
            self._ensure(active_ride is None, 409, "User already has an active ride.")

            picked_vehicle, station_id = await self._pick_vehicle_by_location(
                db, lon, lat
            )

            new_ride_id = str(uuid.uuid4())
            start_time = datetime.now()

            await self.vehicles_repo.mark_vehicle_as_rented(
                db, picked_vehicle.vehicle_id
            )
            await self.rides_repo.create_active_ride(
                db,
                new_ride_id,
                user_id,
                picked_vehicle.vehicle_id,
                station_id,
                start_time,
            )

            return Ride(
                ride_id=new_ride_id,
                user_id=user_id,
                vehicle_id=picked_vehicle.vehicle_id,
                start_time=start_time,
                start_station_id=station_id,
            )
        except HTTPException:
            raise
        except Exception as e:
            raise HTTPException(
                status_code=500, detail=f"Could not start ride: {str(e)}"
            )

    async def end_ride(
        self,
        db: aiosqlite.Connection,
        ride_id: str,
        lon: float,
        lat: float,
    ) -> dict:
        """
        End an active ride with the following flow:
        1. Verify ride exists in active rides
        2. Find nearest station with available capacity
        3. Dock the vehicle at that station
        4. Increment vehicle's ride counter (sets to degraded if > 10)
        5. Charge the user 15 ILS (0 if degraded report)
        6. Clear user's active ride
        """

        # Step 1: Verify ride exists
        ride = await self.rides_repo.get_by_id(db, ride_id)
        if not ride:
            raise HTTPException(
                status_code=404, detail=f"Ride with ID {ride_id} not found."
            )

        # Step 2: Find nearest station with capacity
        stations = await self.stations_service.get_stations_with_capacity(db)
        if not stations:
            raise HTTPException(
                status_code=400, detail="No stations available to dock the vehicle."
            )

        # Filter only stations with free capacity
        available_stations = [
            s for s in stations if s["current_capacity"] < s["max_capacity"]
        ]

        if not available_stations:
            raise HTTPException(
                status_code=400, detail="No station with free capacity available."
            )

        # Find nearest by euclidean distance
        nearest_station = min(
            available_stations,
            key=lambda s: calculate_euclidean_distance(lat, lon, s["lat"], s["lon"]),
        )

        station_id = nearest_station["station_id"]
        end_time = datetime.now()

        # Step 3 & 4: Get vehicle and dock it (incrementing rides counter)
        vehicle = await self.vehicles_repo.get_by_id(db, ride.vehicle_id)
        if not vehicle:
            raise HTTPException(
                status_code=400, detail=f"Vehicle {ride.vehicle_id} not found."
            )

        # Dock the vehicle at the station
        docked_vehicle = await self.vehicles_repo.dock_vehicle(
            db, ride.vehicle_id, station_id
        )
        if not docked_vehicle:
            raise HTTPException(
                status_code=400, detail=f"Failed to dock vehicle {ride.vehicle_id}."
            )

        ride_updated = await self.rides_repo.complete_ride(
            db,
            ride_id=ride_id,
            end_station_id=station_id,
            end_time=end_time,
        )
        if not ride_updated:
            raise HTTPException(
                status_code=409, detail=f"Ride with ID {ride_id} is already ended."
            )

        # Step 5: Calculate and process payment
        # For now, return a fixed 15 ILS
        payment_charged = 15

        # Return response object (only required fields per specification)
        return {
            "end_station_id": station_id,
            "payment_charged": payment_charged,
            "vehicle": docked_vehicle.model_dump(mode="json"),
        }
