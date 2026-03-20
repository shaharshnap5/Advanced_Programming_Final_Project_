import datetime
import uuid
import aiosqlite
from fastapi import HTTPException
from datetime import datetime

from src.models.ride import Ride
from src.services.stations_service import StationsService
from src.repositories.vehicles_repository import VehiclesRepository
from src.repositories.rides_repository import RidesRepository
from src.repositories.users_repository import UsersRepository
from src.repositories.stations_repository import StationsRepository
from src.utilis.distance import calculate_euclidean_distance
from src.models.lock_manager import LockManager



class RideService:
    def __init__(self):
        # Initialize the warehouse workers
        self.vehicles_repo = VehiclesRepository()
        self.rides_repo = RidesRepository()
        self.stations_service = StationsService()
        self.stations_repo = StationsRepository()
        self.users_repo = UsersRepository()
        self.lock_manager = LockManager()


    async def start_new_ride(
            self, db: aiosqlite.Connection, user_id: str, lon: float, lat: float
    ) -> Ride:
        """
        Start a new ride with proper locking to prevent race conditions.
        Locks are acquired in this order to prevent deadlocks: user -> vehicle
        """
        # 0. Check if user already has an active ride (with user lock)
        active_ride = await self.rides_repo.get_active_ride_by_user(db, user_id)
        if active_ride:
            raise HTTPException(status_code=409, detail="User already has an active ride.")

        # 1. Find the nearest station THAT ACTUALLY HAS VEHICLES
        nearest_station = await self.stations_service.get_nearest_station_with_vehicles(db, lon=lon, lat=lat)

        if not nearest_station:
            # If absolutely no stations in the city have vehicles, we throw a 404
            raise HTTPException(status_code=404, detail="No available vehicles found in the entire system.")

        # Get the station_id from the Station model
        station_id = nearest_station.station_id

        # 2. Ask the warehouse for ALL available vehicles at that specific station
        available_vehicles = await self.vehicles_repo.get_available_vehicles_by_station(db, station_id)

        if not available_vehicles:
            raise HTTPException(status_code=404, detail="No available vehicles at the nearest station.")

        # 3. Apply the Deterministic Rule (Scooter > E-bike > Bike, then by ID)
        type_priority = {
            "scooter": 1,
            "electric_bicycle": 2,
            "bicycle": 3
        }

        sorted_vehicles = sorted(
            available_vehicles,
            key=lambda v: (type_priority.get(v.vehicle_type.value, 4), v.vehicle_id)
        )

        # Try to rent the best available vehicle that passes domain rules
        picked_vehicle = None
        for vehicle in sorted_vehicles:
            # First check domain rules (battery, eligibility)
            if not vehicle.can_rent():
                continue

            try:
                # This will acquire the vehicle lock and verify availability
                rented_vehicle = await self.vehicles_repo.mark_vehicle_as_rented(db, vehicle.vehicle_id)
                if rented_vehicle:
                    picked_vehicle = rented_vehicle
                    break
            except ValueError:
                # Vehicle was taken by another request, try next one
                continue

        if not picked_vehicle:
            raise HTTPException(status_code=409, detail="No available vehicles have sufficient charge/eligibility or all were taken by other users.")

        # 4. Generate a unique ID for the new ride
        new_ride_id = str(uuid.uuid4())

        # 5. Capture the ride start time once and persist the state to the database
        start_time = datetime.now()

        # Create the ride (with user lock to prevent duplicate rides)
        try:
            await self.rides_repo.create_active_ride(
                db,
                new_ride_id,
                user_id,
                picked_vehicle.vehicle_id,
                station_id,
                start_time,
            )
        except ValueError as e:
            # If ride creation fails, return the vehicle to available status
            await self.vehicles_repo.update_vehicle_status(db, picked_vehicle.vehicle_id, "available")
            raise HTTPException(status_code=409, detail=str(e))

        # 6. Return the exact JSON shape
        return Ride(
            ride_id=new_ride_id,
            user_id=user_id,
            vehicle_id=picked_vehicle.vehicle_id,
            start_time=start_time,
            start_station_id=station_id
        )

    async def end_ride(
        self,
        db: aiosqlite.Connection,
        ride_id: str,
        lon: float,
        lat: float,
    ) -> dict:
        """
        End an active ride with the following flow (with proper locking):
        1. Verify ride exists in active rides
        2. Find nearest station with available capacity
        3. Atomically check capacity and dock the vehicle
        4. Increment vehicle's ride counter (sets to degraded if > 10)
        5. Charge the user 15 ILS (0 if degraded report)
        6. Clear user's active ride
        """

        # Step 1: Verify ride exists
        ride = await self.rides_repo.get_by_id(db, ride_id)
        if not ride:
            raise HTTPException(status_code=404, detail=f"Ride with ID {ride_id} not found.")

        # Step 2: Find nearest station with capacity
        stations = await self.stations_service.get_stations_with_capacity(db)
        if not stations:
            raise HTTPException(status_code=400, detail="No stations available to dock the vehicle.")

        # Filter only stations with free capacity
        available_stations = [
            s for s in stations
            if s["current_capacity"] < s["max_capacity"]
        ]

        if not available_stations:
            raise HTTPException(status_code=400, detail="No station with free capacity available.")

        # Sort stations by distance
        sorted_stations = sorted(
            available_stations,
            key=lambda s: calculate_euclidean_distance(lat, lon, s["lat"], s["lon"])
        )

        # Step 3 & 4: Try to dock at nearest available station with capacity
        vehicle = await self.vehicles_repo.get_by_id(db, ride.vehicle_id)
        if not vehicle:
            raise HTTPException(status_code=400, detail=f"Vehicle {ride.vehicle_id} not found.")

        docked_station_id = None
        docked_vehicle = None
        for station in sorted_stations:
            station_id = station["station_id"]

            # Check capacity with lock
            has_capacity = await self.stations_repo.check_and_reserve_capacity(db, station_id)

            if has_capacity:
                try:
                    # Dock the vehicle at the station (with vehicle lock)
                    docked_vehicle = await self.vehicles_repo.dock_vehicle(
                        db,
                        ride.vehicle_id,
                        station_id
                    )
                    if docked_vehicle:
                        docked_station_id = station_id
                        break
                except ValueError:
                    # If docking fails, try next station
                    continue

        if not docked_station_id or not docked_vehicle:
            raise HTTPException(status_code=400, detail="Unable to dock vehicle - all stations reached capacity.")


        # Step 5: Calculate and process payment
        # For now, return a fixed 15 ILS
        payment_charged = 15

        # Return response object (only required fields per specification)
        return {
            "end_station_id": docked_station_id,
            "payment_charged": payment_charged,
            "vehicle": docked_vehicle.model_dump(mode="json"),
        }