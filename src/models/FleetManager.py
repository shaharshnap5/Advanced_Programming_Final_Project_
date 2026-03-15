import asyncio
from typing import Dict
from .station import Station
from .user import User
from .ride import Ride


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
        pass

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