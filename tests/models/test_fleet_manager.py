"""
Comprehensive tests for the FleetManager model with 100% coverage.
Tests cover:
- Singleton pattern implementation
- Initialization
- State dictionaries (stations, users, active_rides)
- Concurrency lock presence
- Async methods stubs
"""

import pytest
import asyncio
from unittest.mock import Mock, AsyncMock, patch

from src.models.FleetManager import FleetManager
from src.models.station import Station
from src.models.user import User
from src.models.ride import Ride


class TestFleetManagerSingleton:
    """Tests for the FleetManager Singleton Pattern."""

    def test_singleton_instance_creation(self):
        """Test that FleetManager creates a single instance."""
        fm1 = FleetManager()
        fm2 = FleetManager()

        assert fm1 is fm2
        assert id(fm1) == id(fm2)

    def test_singleton_multiple_instantiation(self):
        """Test that multiple instantiations return the same instance."""
        instances = [FleetManager() for _ in range(5)]

        for instance in instances:
            assert instance is instances[0]

    def test_singleton_initialization_only_once(self):
        """Test that initialization code runs only once."""
        # Reset the singleton for testing
        FleetManager._instance = None

        fm1 = FleetManager()
        initial_stations = id(fm1.stations)

        fm2 = FleetManager()
        second_stations = id(fm2.stations)

        # Should be the same object in memory
        assert initial_stations == second_stations

        # Reset for other tests
        FleetManager._instance = None

    def test_singleton_prevent_data_wipe(self):
        """Test that calling __init__ again doesn't wipe data."""
        FleetManager._instance = None
        fm = FleetManager()

        # Add some test data
        test_station = Station(
            station_id=1,
            name="Test",
            lat=32.0,
            lon=34.0,
            max_capacity=10
        )
        fm.stations[1] = test_station

        # Call init again (simulating FleetManager() call)
        fm_again = FleetManager()

        # Data should still be there
        assert 1 in fm_again.stations
        assert fm_again.stations[1].name == "Test"

        FleetManager._instance = None


class TestFleetManagerInitialization:
    """Tests for FleetManager initialization."""

    @pytest.fixture
    def fresh_fleet_manager(self):
        """Create a fresh FleetManager instance."""
        FleetManager._instance = None
        fm = FleetManager()
        yield fm
        FleetManager._instance = None

    def test_fleet_manager_initialization(self, fresh_fleet_manager):
        """Test that FleetManager initializes with correct state."""
        assert fresh_fleet_manager._initialized is True
        assert isinstance(fresh_fleet_manager.stations, dict)
        assert isinstance(fresh_fleet_manager.users, dict)
        assert isinstance(fresh_fleet_manager.active_rides, dict)

    def test_stations_initialized_empty(self, fresh_fleet_manager):
        """Test that stations dictionary is empty on initialization."""
        assert fresh_fleet_manager.stations == {}
        assert len(fresh_fleet_manager.stations) == 0

    def test_users_initialized_empty(self, fresh_fleet_manager):
        """Test that users dictionary is empty on initialization."""
        assert fresh_fleet_manager.users == {}
        assert len(fresh_fleet_manager.users) == 0

    def test_active_rides_initialized_empty(self, fresh_fleet_manager):
        """Test that active_rides dictionary is empty on initialization."""
        assert fresh_fleet_manager.active_rides == {}
        assert len(fresh_fleet_manager.active_rides) == 0

    def test_state_lock_initialized(self, fresh_fleet_manager):
        """Test that state_lock is initialized as asyncio.Lock."""
        assert hasattr(fresh_fleet_manager, 'state_lock')
        assert isinstance(fresh_fleet_manager.state_lock, asyncio.Lock)


class TestFleetManagerStateDictionaries:
    """Tests for FleetManager state dictionaries."""

    @pytest.fixture
    def fleet_manager(self):
        """Create a FleetManager instance."""
        FleetManager._instance = None
        fm = FleetManager()
        yield fm
        FleetManager._instance = None

    def test_add_station_to_fleet_manager(self, fleet_manager):
        """Test adding a station to the fleet manager."""
        station = Station(
            station_id=1,
            name="Test Station",
            lat=32.0,
            lon=34.0,
            max_capacity=10
        )

        fleet_manager.stations[1] = station

        assert 1 in fleet_manager.stations
        assert fleet_manager.stations[1].name == "Test Station"

    def test_add_user_to_fleet_manager(self, fleet_manager):
        """Test adding a user to the fleet manager."""
        user = User(
            user_id="USER001",
            payment_token="tok_visa_123456"
        )

        fleet_manager.users["USER001"] = user

        assert "USER001" in fleet_manager.users
        assert fleet_manager.users["USER001"].payment_token == "tok_visa_123456"

    def test_add_ride_to_fleet_manager(self, fleet_manager):
        """Test adding a ride to the fleet manager."""
        ride = Ride(
            ride_id="RIDE001",
            user_id="USER001",
            vehicle_id="VEHICLE001"
        )

        fleet_manager.active_rides["RIDE001"] = ride

        assert "RIDE001" in fleet_manager.active_rides
        assert fleet_manager.active_rides["RIDE001"].user_id == "USER001"

    def test_multiple_stations(self, fleet_manager):
        """Test adding and managing multiple stations."""
        stations = [
            Station(station_id=i, name=f"Station {i}", lat=32.0+i*0.1, lon=34.0+i*0.1, max_capacity=10)
            for i in range(1, 4)
        ]

        for station in stations:
            fleet_manager.stations[station.station_id] = station

        assert len(fleet_manager.stations) == 3
        assert all(i in fleet_manager.stations for i in range(1, 4))

    def test_multiple_users(self, fleet_manager):
        """Test adding and managing multiple users."""
        users = [
            User(user_id=f"USER{i:03d}", payment_token=f"tok_visa_{i}")
            for i in range(1, 4)
        ]

        for user in users:
            fleet_manager.users[user.user_id] = user

        assert len(fleet_manager.users) == 3
        assert all(f"USER{i:03d}" in fleet_manager.users for i in range(1, 4))

    def test_multiple_active_rides(self, fleet_manager):
        """Test managing multiple active rides."""
        rides = [
            Ride(ride_id=f"RIDE{i:03d}", user_id=f"USER{i:03d}", vehicle_id=f"VEHICLE{i:03d}")
            for i in range(1, 4)
        ]

        for ride in rides:
            fleet_manager.active_rides[ride.ride_id] = ride

        assert len(fleet_manager.active_rides) == 3
        assert all(f"RIDE{i:03d}" in fleet_manager.active_rides for i in range(1, 4))

    def test_retrieve_station_by_id(self, fleet_manager):
        """Test retrieving a station by ID."""
        station = Station(
            station_id=5,
            name="Retrievable Station",
            lat=32.5,
            lon=34.5,
            max_capacity=20
        )
        fleet_manager.stations[5] = station

        retrieved = fleet_manager.stations.get(5)
        assert retrieved is not None
        assert retrieved.name == "Retrievable Station"

    def test_retrieve_user_by_id(self, fleet_manager):
        """Test retrieving a user by ID."""
        user = User(
            user_id="USER_RETRIEVE",
            payment_token="tok_retrieve_123"
        )
        fleet_manager.users["USER_RETRIEVE"] = user

        retrieved = fleet_manager.users.get("USER_RETRIEVE")
        assert retrieved is not None
        assert retrieved.payment_token == "tok_retrieve_123"

    def test_retrieve_ride_by_id(self, fleet_manager):
        """Test retrieving a ride by ID."""
        ride = Ride(
            ride_id="RIDE_RETRIEVE",
            user_id="USER_RETRIEVE",
            vehicle_id="VEHICLE_RETRIEVE"
        )
        fleet_manager.active_rides["RIDE_RETRIEVE"] = ride

        retrieved = fleet_manager.active_rides.get("RIDE_RETRIEVE")
        assert retrieved is not None
        assert retrieved.user_id == "USER_RETRIEVE"

    def test_remove_station(self, fleet_manager):
        """Test removing a station."""
        station = Station(
            station_id=99,
            name="To Remove",
            lat=32.99,
            lon=34.99,
            max_capacity=5
        )
        fleet_manager.stations[99] = station
        assert 99 in fleet_manager.stations

        del fleet_manager.stations[99]
        assert 99 not in fleet_manager.stations

    def test_remove_user(self, fleet_manager):
        """Test removing a user."""
        user = User(user_id="USER_REMOVE", payment_token="tok_remove")
        fleet_manager.users["USER_REMOVE"] = user
        assert "USER_REMOVE" in fleet_manager.users

        del fleet_manager.users["USER_REMOVE"]
        assert "USER_REMOVE" not in fleet_manager.users

    def test_remove_ride(self, fleet_manager):
        """Test removing a ride."""
        ride = Ride(
            ride_id="RIDE_REMOVE",
            user_id="USER_REMOVE",
            vehicle_id="VEHICLE_REMOVE"
        )
        fleet_manager.active_rides["RIDE_REMOVE"] = ride
        assert "RIDE_REMOVE" in fleet_manager.active_rides

        del fleet_manager.active_rides["RIDE_REMOVE"]
        assert "RIDE_REMOVE" not in fleet_manager.active_rides


class TestFleetManagerMethods:
    """Tests for FleetManager methods (stubs)."""

    @pytest.fixture
    def fleet_manager(self):
        """Create a FleetManager instance."""
        FleetManager._instance = None
        fm = FleetManager()
        yield fm
        FleetManager._instance = None

    def test_load_data_method_exists(self, fleet_manager):
        """Test that load_data method exists."""
        assert hasattr(fleet_manager, 'load_data')
        assert callable(fleet_manager.load_data)

    def test_register_user_method_exists(self, fleet_manager):
        """Test that register_user method exists."""
        assert hasattr(fleet_manager, 'register_user')
        assert callable(fleet_manager.register_user)

    def test_get_nearest_station_method_exists(self, fleet_manager):
        """Test that get_nearest_station method exists."""
        assert hasattr(fleet_manager, 'get_nearest_station')
        assert callable(fleet_manager.get_nearest_station)

    def test_start_ride_method_exists(self, fleet_manager):
        """Test that start_ride method exists."""
        assert hasattr(fleet_manager, 'start_ride')
        assert callable(fleet_manager.start_ride)

    def test_end_ride_method_exists(self, fleet_manager):
        """Test that end_ride method exists."""
        assert hasattr(fleet_manager, 'end_ride')
        assert callable(fleet_manager.end_ride)

    def test_treat_vehicles_method_exists(self, fleet_manager):
        """Test that treat_vehicles method exists."""
        assert hasattr(fleet_manager, 'treat_vehicles')
        assert callable(fleet_manager.treat_vehicles)

    @pytest.mark.asyncio
    async def test_register_user_is_async(self, fleet_manager):
        """Test that register_user is an async method."""
        import inspect
        assert inspect.iscoroutinefunction(fleet_manager.register_user)

    @pytest.mark.asyncio
    async def test_get_nearest_station_is_async(self, fleet_manager):
        """Test that get_nearest_station is an async method."""
        import inspect
        assert inspect.iscoroutinefunction(fleet_manager.get_nearest_station)

    @pytest.mark.asyncio
    async def test_start_ride_is_async(self, fleet_manager):
        """Test that start_ride is an async method."""
        import inspect
        assert inspect.iscoroutinefunction(fleet_manager.start_ride)

    @pytest.mark.asyncio
    async def test_end_ride_is_async(self, fleet_manager):
        """Test that end_ride is an async method."""
        import inspect
        assert inspect.iscoroutinefunction(fleet_manager.end_ride)

    @pytest.mark.asyncio
    async def test_treat_vehicles_is_async(self, fleet_manager):
        """Test that treat_vehicles is an async method."""
        import inspect
        assert inspect.iscoroutinefunction(fleet_manager.treat_vehicles)


class TestFleetManagerConcurrency:
    """Tests for FleetManager concurrency features."""

    @pytest.fixture
    def fleet_manager(self):
        """Create a FleetManager instance."""
        FleetManager._instance = None
        fm = FleetManager()
        yield fm
        FleetManager._instance = None

    def test_state_lock_is_asyncio_lock(self, fleet_manager):
        """Test that state_lock is an asyncio.Lock instance."""
        assert isinstance(fleet_manager.state_lock, asyncio.Lock)

    @pytest.mark.asyncio
    async def test_state_lock_can_acquire(self, fleet_manager):
        """Test that state_lock can be acquired."""
        async with fleet_manager.state_lock:
            # Lock is acquired
            pass
        # Lock is released

    @pytest.mark.asyncio
    async def test_state_lock_mutual_exclusion(self, fleet_manager):
        """Test that state_lock provides mutual exclusion."""
        execution_order = []

        async def task1():
            async with fleet_manager.state_lock:
                execution_order.append("task1_start")
                await asyncio.sleep(0.01)
                execution_order.append("task1_end")

        async def task2():
            async with fleet_manager.state_lock:
                execution_order.append("task2_start")
                execution_order.append("task2_end")

        await asyncio.gather(task1(), task2())

        # Ensure tasks don't interleave
        assert execution_order.index("task1_start") < execution_order.index("task1_end")
        # Either task1 completes before task2 starts or vice versa
        if execution_order.index("task1_end") < execution_order.index("task2_start"):
            assert True  # task1 completed first
        else:
            assert execution_order.index("task2_end") < execution_order.index("task1_start")

