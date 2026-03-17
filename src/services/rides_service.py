from __future__ import annotations

from fastapi import HTTPException

from src.models.FleetManager import FleetManager
from src.models.ride import Ride
from src.models.station import Station
from src.models.user import User
from src.services.stations_service import StationsService
from src.services.users_service import UsersService
from src.services.vehicles_service import VehiclesService


class RidesService:
    def __init__(
        self,
        stations_service: StationsService | None = None,
        users_service: UsersService | None = None,
        vehicles_service: VehiclesService | None = None,
    ) -> None:
        self._stations_service = stations_service or StationsService()
        self._users_service = users_service or UsersService()
        self._vehicles_service = vehicles_service or VehiclesService()

    async def end_ride(self, db, ride_id: str, lon: float, lat: float) -> dict:
        """End a ride by docking the vehicle, charging the user, and returning the destination."""
        fm = FleetManager()
        ride: Ride | None = fm.active_rides.get(ride_id)
        if not ride:
            raise HTTPException(status_code=404, detail="Ride not found")

        # Find the nearest available station with a free locking spot
        async with fm.state_lock:
            station: Station | None = await self._stations_service.get_nearest_station_with_capacity(
                db, lon, lat
            )

            if not station:
                raise HTTPException(
                    status_code=400, detail="No station with free locking spots"
                )

            # Dock vehicle: update vehicle record and update ride count/state
            vehicle = await self._vehicles_service.get_vehicle_by_id(db, ride.vehicle_id)
            if not vehicle:
                raise HTTPException(status_code=404, detail="Vehicle not found")

            new_rides = vehicle["rides_since_last_treated"] + 1
            new_status = "degraded" if new_rides > 10 else "available"

            await self._vehicles_service.dock_vehicle(
                db,
                ride.vehicle_id,
                station.station_id,
                new_rides,
                new_status,
            )

            # Charge user
            user_record = await self._users_service.get_user_by_id(db, ride.user_id)
            if not user_record:
                raise HTTPException(status_code=404, detail="User not found")

            user = User.model_validate(user_record)
            cost = ride.calculate_cost()
            user.charge(cost)
            await self._users_service.clear_current_ride(db, ride.user_id)

            # Remove from active rides
            del fm.active_rides[ride_id]

        active_users = [r.user_id for r in fm.active_rides.values()]

        return {
            "end_station_id": station.station_id,
            "end_station": station,
            "payment_charged": cost,
            "active_users": active_users,
        }
