import datetime
import uuid
import aiosqlite
from fastapi import HTTPException
from datetime import datetime

from src.models.ride import Ride
from src.services.stations_service import StationsService
from src.repositories.vehicles_repository import VehiclesRepository
from src.repositories.rides_repository import RidesRepository



class RideService:
    def __init__(self):
        # Initialize the warehouse workers
        self.vehicles_repo = VehiclesRepository()
        self.rides_repo = RidesRepository()
        self.stations_service = StationsService()


    async def start_new_ride(
            self, db: aiosqlite.Connection, user_id: str, lon: float, lat: float
    ) -> Ride:
        # 1. Find the nearest station THAT ACTUALLY HAS VEHICLES
        nearest_station = await self.stations_service.get_nearest_station_with_vehicles(db, lon=lon, lat=lat)

        if not nearest_station:
            # If absolutely no stations in the city have vehicles, we throw a 404
            raise HTTPException(status_code=404, detail="No available vehicles found in the entire system.")

        # Get the station_id from the Station model
        station_id = nearest_station.station_id

        # 2. Ask the warehouse for ALL available vehicles at that specific station
        available_vehicles = await self.vehicles_repo.get_available_vehicles_by_station(db, station_id)

        # 3. Apply the Deterministic Rule (Scooter > E-bike > Bike, then by ID)
        type_priority = {
            "scooter": 1,
            "electric_bicycle": 2,
            "bicycle": 3
        }

        # 👇 FIX 1: Bracket notation inside the lambda function 👇
        sorted_vehicles = sorted(
            available_vehicles,
            key=lambda v: (type_priority.get(v.vehicle_type, 4), v.vehicle_id)
        )

        # Pick the absolute best vehicle from the top of the sorted list
        picked_vehicle = sorted_vehicles[0]

        # 4. Generate a unique ID for the new ride
        new_ride_id = str(uuid.uuid4())

        # 5. Capture the ride start time once and persist the state to the database
        start_time = datetime.now()
        # 👇 FIX 2: Bracket notation for the database calls 👇
        await self.vehicles_repo.mark_vehicle_as_rented(db, picked_vehicle.vehicle_id)
        await self.rides_repo.create_active_ride(
            db,
            new_ride_id,
            user_id,
            picked_vehicle.vehicle_id,
            station_id,
            start_time,
        )

        # 6. Return the exact JSON shape
        # 👇 FIX 3: Use the captured start_time instead of calling datetime.now() again 👇
        return Ride(
            ride_id=new_ride_id,
            user_id=user_id,
            vehicle_id=picked_vehicle.vehicle_id,
            start_time=start_time,
            start_station_id=station_id
        )