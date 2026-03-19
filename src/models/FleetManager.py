import asyncio
import csv
from typing import Dict
from datetime import datetime
from .station import Station
from .user import User
from .ride import Ride
from .vehicle import Vehicle, VehicleType, VehicleStatus


class FleetManager:
    _instance = None

    # 1. The Singleton Pattern
    def __new__(cls):
        """Ensures only one instance of FleetManager exists in memory."""
        if cls._instance is None:
            cls._instance = super(FleetManager, cls).__new__(cls)
            cls._instance._initialized = False
        return cls._instance

    def __init__(self):
        # Prevent wiping the data if FleetManager() is called again
        if self._initialized:
            return

        # 2. In-Memory State Dictionaries
        self.stations: Dict[int, Station] = {}  # [cite: 334]
        self.vehicles: Dict[str, Vehicle] = {}  # Store all vehicles by vehicle_id
        self.users: Dict[str, User] = {}  # [cite: 335]
        self.active_rides: Dict[str, Ride] = {}  # [cite: 336]

        # 3. Concurrency Lock
        # Required to manage locks on concurrent requests [cite: 173]
        # Prevents race conditions when two users try to rent the same vehicle 
        self.state_lock = asyncio.Lock()

        self._initialized = True

    # 4. The Core Methods (Async)
    def load_data(self, stations_file: str, vehicles_file: str) -> None:
        """Loads CSV data and wires vehicles to stations using a Factory Method. [cite: 338, 404]"""
        # Load stations
        with open(stations_file, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            for row in reader:
                station_id = int(row['station_id'])
                station = Station(
                    station_id=station_id,
                    name=row['name'],
                    lat=float(row['lat']),
                    lon=float(row['lon']),
                    max_capacity=int(row['max_capacity']),
                    vehicles=[]
                )
                self.stations[station_id] = station

        # Load vehicles and wire them to stations
        with open(vehicles_file, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            for row in reader:
                vehicle_id = row['vehicle_id']
                station_id = int(row['station_id']) if row['station_id'] else None
                vehicle_type = VehicleType(row['vehicle_type'])
                status = VehicleStatus(row['status'])
                rides_since_last_treated = int(row['rides_since_last_treated'])
                last_treated_date = datetime.strptime(row['last_treated_date'], '%Y-%m-%d').date() if row['last_treated_date'] else None

                # Create vehicle (basic Vehicle for now, can be extended with Factory Method)
                vehicle = Vehicle(
                    vehicle_id=vehicle_id,
                    station_id=station_id,
                    vehicle_type=vehicle_type,
                    status=status,
                    rides_since_last_treated=rides_since_last_treated,
                    last_treated_date=last_treated_date
                )

                # Store vehicle in state
                self.vehicles[vehicle_id] = vehicle

                # Wire vehicle to station if it has a station_id
                if station_id and station_id in self.stations:
                    self.stations[station_id].vehicles.append(vehicle_id)

    async def register_user(self, name: str, credit_token: str) -> User:
        """Registers user & payment method. [cite: 104, 105, 339]"""
        pass

    async def get_nearest_station(self, lat: float, lon: float) -> Station:
        """Finds the nearest station using Euclidean distance. [cite: 82, 340]"""
        pass

    async def start_ride(self, user_id: str, lat: float, lon: float) -> Ride:
        """Handles vehicle eligibility, deterministic selection, and docking logic. [cite: 82, 83, 341]"""
        pass

    async def end_ride(self, user_id: str, lat: float, lon: float) -> None:
        """Docks vehicle, increments ride counter, and processes payment. [cite: 89, 91, 342]"""
        pass

    async def treat_vehicles(self) -> list[str]:
        """Runs maintenance on eligible vehicles and returns treated IDs. [cite: 125, 126]"""
        pass