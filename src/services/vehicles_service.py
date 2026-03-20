from __future__ import annotations

import aiosqlite

from src.repositories.vehicles_repository import VehiclesRepository
from src.models.vehicle import Vehicle, VehicleStatus

class VehiclesService:
    def __init__(self, repository: VehiclesRepository | None = None) -> None:
        self._repository = repository or VehiclesRepository()

    async def get_vehicle_by_id(self, db: aiosqlite.Connection, vehicle_id: str) -> Vehicle | None:
        return await self._repository.get_by_id(db, vehicle_id)

    async def report_vehicle_degraded(self, db: aiosqlite.Connection, vehicle_id: str) -> Vehicle:
        """Marks a vehicle as degraded due to user report."""
        vehicle = await self.get_vehicle_by_id(db, vehicle_id)
        if not vehicle:
            raise ValueError(f"Vehicle {vehicle_id} not found")

        if vehicle.status == VehicleStatus.degraded:
            raise ValueError(f"Vehicle {vehicle_id} is already marked as degraded")

        success = await self._repository.update_vehicle_status(db, vehicle_id, VehicleStatus.degraded)
        if not success:
            raise Exception(f"Failed to report vehicle {vehicle_id} as degraded")

        return await self.get_vehicle_by_id(db, vehicle_id)

    async def treat_vehicle(self, db: aiosqlite.Connection, vehicle_id: str, station_id: int | None = None) -> Vehicle:
        """Perform maintenance on a vehicle.
        Requirements:
        - Vehicle must be degraded OR have >= 7 rides since last treatment
        - Treatment sets: status='available', rides_since_last_treated=0, last_treated_date=today
        - If vehicle was degraded (no station), assign a station
        """
        # Get the vehicle
        vehicle = await self.get_vehicle_by_id(db, vehicle_id)
        if not vehicle:
            raise ValueError(f"Vehicle {vehicle_id} not found")

        # Check eligibility for treatment
        is_degraded = vehicle.status == VehicleStatus.degraded
        rides_threshold_met = vehicle.rides_since_last_treated >= 7

        if not (is_degraded or rides_threshold_met):
            raise ValueError(
                f"Vehicle {vehicle_id} is not eligible for treatment. "
                f"Status: {vehicle.status}, Rides: {vehicle.rides_since_last_treated}. "
                f"Must be degraded or have >= 7 rides."
            )

        # For previously degraded vehicles, a station must be assigned
        if is_degraded and not vehicle.station_id and not station_id:
            raise ValueError(
                f"Vehicle {vehicle_id} was degraded without a station. "
                f"Must provide a station_id to assign it a location."
            )

        # Use provided station_id or keep existing one
        treatment_station = station_id if station_id else vehicle.station_id

        # Perform treatment
        success = await self._repository.treat_vehicle(db, vehicle_id, treatment_station)
        if not success:
            raise Exception(f"Failed to treat vehicle {vehicle_id}")

        # Return updated vehicle
        return await self.get_vehicle_by_id(db, vehicle_id)
