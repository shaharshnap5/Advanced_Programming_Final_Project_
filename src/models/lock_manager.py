"""
Centralized lock manager for handling concurrent access to shared resources.
Provides locks for vehicles, users, stations, and rides to prevent race conditions.
"""
import asyncio
from typing import Dict, Union
from contextlib import asynccontextmanager


class LockManager:
    """
    Thread-safe lock manager for managing concurrent access to resources.
    Uses asyncio locks to ensure atomic operations on shared resources.
    Implemented as a singleton to ensure consistent locking across the application.
    """

    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            # Initialize only once
            cls._instance._vehicle_locks: Dict[str, asyncio.Lock] = {}
            cls._instance._user_locks: Dict[str, asyncio.Lock] = {}
            cls._instance._station_locks: Dict[int, asyncio.Lock] = {}
            cls._instance._ride_locks: Dict[str, asyncio.Lock] = {}

            # Master locks to protect the lock dictionaries themselves
            cls._instance._vehicle_master_lock = asyncio.Lock()
            cls._instance._user_master_lock = asyncio.Lock()
            cls._instance._station_master_lock = asyncio.Lock()
            cls._instance._ride_master_lock = asyncio.Lock()
        return cls._instance

    @asynccontextmanager
    async def _generic_lock(
        self,
        resource_id: Union[str, int],
        locks_dict: Dict,
        master_lock: asyncio.Lock
    ):
        """
        Generic lock acquisition for any resource type.

        Args:
            resource_id: The ID of the resource to lock
            locks_dict: The dictionary storing locks for this resource type
            master_lock: The master lock protecting the locks dictionary
        """
        async with master_lock:
            if resource_id not in locks_dict:
                locks_dict[resource_id] = asyncio.Lock()
            lock = locks_dict[resource_id]

        async with lock:
            try:
                yield
            finally:
                pass

    @asynccontextmanager
    async def vehicle_lock(self, vehicle_id: str):
        """
        Acquire a lock for a specific vehicle to prevent concurrent modifications.

        Usage:
            async with lock_manager.vehicle_lock(vehicle_id):
                # Perform vehicle operations
                pass
        """
        async with self._generic_lock(vehicle_id, self._vehicle_locks, self._vehicle_master_lock):
            yield

    @asynccontextmanager
    async def user_lock(self, user_id: str):
        """
        Acquire a lock for a specific user to prevent concurrent ride operations.

        Usage:
            async with lock_manager.user_lock(user_id):
                # Check and modify user's active ride
                pass
        """
        async with self._generic_lock(user_id, self._user_locks, self._user_master_lock):
            yield

    @asynccontextmanager
    async def station_lock(self, station_id: int):
        """
        Acquire a lock for a specific station to prevent concurrent capacity issues.

        Usage:
            async with lock_manager.station_lock(station_id):
                # Check capacity and dock vehicle
                pass
        """
        async with self._generic_lock(station_id, self._station_locks, self._station_master_lock):
            yield

    @asynccontextmanager
    async def ride_lock(self, ride_id: str):
        """
        Acquire a lock for a specific ride to prevent concurrent modifications.

        Usage:
            async with lock_manager.ride_lock(ride_id):
                # Modify ride state
                pass
        """
        async with self._generic_lock(ride_id, self._ride_locks, self._ride_master_lock):
            yield

    @asynccontextmanager
    async def multi_vehicle_lock(self, *vehicle_ids: str):
        """
        Acquire locks for multiple vehicles in a consistent order to prevent deadlocks.
        Vehicles are sorted by ID to ensure consistent lock ordering.

        Usage:
            async with lock_manager.multi_vehicle_lock(vehicle_id1, vehicle_id2):
                # Perform operations on multiple vehicles
                pass
        """
        # Sort to prevent deadlocks
        sorted_ids = sorted(set(vehicle_ids))

        # Acquire all locks
        async with self._vehicle_master_lock:
            locks = []
            for vehicle_id in sorted_ids:
                if vehicle_id not in self._vehicle_locks:
                    self._vehicle_locks[vehicle_id] = asyncio.Lock()
                locks.append(self._vehicle_locks[vehicle_id])

        # Acquire locks in order
        for lock in locks:
            await lock.acquire()

        try:
            yield
        finally:
            # Release in reverse order
            for lock in reversed(locks):
                lock.release()


def get_lock_manager() -> LockManager:
    """Get the global lock manager instance."""
    return LockManager()
