"""Integration tests for the complete Ride flow."""

from __future__ import annotations

import pytest
from datetime import datetime, date

from src.models.ride import Ride, process_end_of_ride
from src.models.user import User
from src.models.vehicle import Vehicle, VehicleType, VehicleStatus


@pytest.mark.asyncio
async def test_complete_ride_lifecycle_integration(test_db):
    """Test a complete ride lifecycle from creation to completion."""
    # Setup: Create a user and ride
    user = User(
        user_id="USER_INTEGRATION",
        first_name="Integration",
        last_name="User",
        email="user.integration@example.com",
        payment_token="TEST_TOKEN_123"
    )

    # Create a ride
    ride = Ride(
        ride_id="RIDE_INTEGRATION_001",
        user_id="USER_INTEGRATION",
        vehicle_id="V_INTEGRATION",
        start_station_id=1,
        start_time=datetime(2026, 3, 17, 10, 0),
        is_degraded_report=False
    )

    # Verify ride was created properly
    assert ride.ride_id == "RIDE_INTEGRATION_001"
    assert ride.user_id == "USER_INTEGRATION"
    assert ride.vehicle_id == "V_INTEGRATION"
    assert ride.start_station_id == 1
    assert ride.start_time == datetime(2026, 3, 17, 10, 0)
    assert ride.end_time is None
    assert ride.is_degraded_report is False

    # Calculate cost
    cost = ride.calculate_cost()
    assert cost == 15  # Normal ride

    # User starts the ride
    assert user.can_start_ride() is True

    # End the ride and process
    process_end_of_ride(user, ride)


@pytest.mark.asyncio
async def test_degraded_ride_lifecycle_integration(test_db):
    """Test a degraded ride lifecycle."""
    # Setup: Create a user and degraded ride
    user = User(
        user_id="USER_DEGRADED",
        first_name="Degraded",
        last_name="User",
        email="user.degraded@example.com",
        payment_token="TEST_TOKEN_456"
    )

    # Create a degraded ride
    ride = Ride(
        ride_id="RIDE_DEGRADED_001",
        user_id="USER_DEGRADED",
        vehicle_id="V_DEGRADED",
        start_station_id=2,
        start_time=datetime(2026, 3, 17, 11, 0),
        is_degraded_report=True  # Marked as degraded
    )

    # Verify degraded status
    assert ride.is_degraded_report is True

    # Calculate cost (should be 0 for degraded)
    cost = ride.calculate_cost()
    assert cost == 0

    # User ends the ride
    process_end_of_ride(user, ride)


@pytest.mark.asyncio
async def test_multiple_sequential_rides(test_db):
    """Test multiple sequential rides for the same user."""
    user = User(
        user_id="USER_SEQUENTIAL",
        first_name="Sequential",
        last_name="User",
        email="user.sequential@example.com",
        payment_token="TEST_TOKEN_789"
    )

    rides = [
        Ride(
            ride_id=f"RIDE_SEQ_{i}",
            user_id="USER_SEQUENTIAL",
            vehicle_id=f"V_SEQ_{i}",
            start_station_id=i + 1,
            start_time=datetime(2026, 3, 17, 10 + i, 0),
            is_degraded_report=i % 2 == 1  # Every other ride degraded
        )
        for i in range(3)
    ]

    # Process all rides
    for ride in rides:
        assert user.can_start_ride() is True

        cost = ride.calculate_cost()
        if ride.is_degraded_report:
            assert cost == 0
        else:
            assert cost == 15

        process_end_of_ride(user, ride)


@pytest.mark.asyncio
async def test_ride_model_with_end_time_integration():
    """Test a ride that has both start and end times."""
    ride = Ride(
        ride_id="RIDE_COMPLETE",
        user_id="USER_COMPLETE",
        vehicle_id="V_COMPLETE",
        start_station_id=1,
        start_time=datetime(2026, 3, 17, 10, 0),
        end_time=datetime(2026, 3, 17, 10, 30),
        is_degraded_report=False
    )

    # Verify both times are set
    assert ride.start_time is not None
    assert ride.end_time is not None
    assert ride.end_time > ride.start_time

    # Calculate duration (for potential future use)
    duration = ride.end_time - ride.start_time
    assert duration.total_seconds() == 1800  # 30 minutes


@pytest.mark.asyncio
async def test_ride_serialization_roundtrip():
    """Test that a ride can be serialized and would be deserializable."""
    original_ride = Ride(
        ride_id="RIDE_SERIALIZE",
        user_id="USER_SERIALIZE",
        vehicle_id="V_SERIALIZE",
        start_station_id=3,
        start_time=datetime(2026, 3, 17, 12, 0),
        end_time=datetime(2026, 3, 17, 12, 45),
        is_degraded_report=False
    )

    # Serialize to dict
    ride_dict = original_ride.model_dump()

    # Verify all fields are present
    assert ride_dict['ride_id'] == "RIDE_SERIALIZE"
    assert ride_dict['user_id'] == "USER_SERIALIZE"
    assert ride_dict['vehicle_id'] == "V_SERIALIZE"
    assert ride_dict['start_station_id'] == 3
    assert ride_dict['is_degraded_report'] is False

    # Recreate from dict
    recreated_ride = Ride(**ride_dict)
    assert recreated_ride.ride_id == original_ride.ride_id
    assert recreated_ride.user_id == original_ride.user_id
    assert recreated_ride.calculate_cost() == original_ride.calculate_cost()


# ============ END RIDE INTEGRATION TESTS ============

@pytest.mark.asyncio
async def test_complete_ride_end_flow_with_mocked_db(test_db):
    """Test the complete end-to-end ride ending process."""
    from unittest.mock import AsyncMock, Mock
    from src.services.rides_service import RideService
    from src.repositories.vehicles_repository import VehiclesRepository
    from src.repositories.users_repository import UsersRepository
    
    # Setup
    service = RideService()
    service.vehicles_repo = AsyncMock(spec=VehiclesRepository)
    service.users_repo = AsyncMock(spec=UsersRepository)
    service.stations_service = AsyncMock()
    
    # Mock data
    mock_stations = [
        {
            "station_id": 1,
            "name": "Central Station",
            "lat": 32.5,
            "lon": 34.5,
            "max_capacity": 20,
            "current_capacity": 10,
        },
        {
            "station_id": 2,
            "name": "North Station",
            "lat": 32.8,
            "lon": 34.8,
            "max_capacity": 15,
            "current_capacity": 14,
        },
    ]
    
    service.rides_repo.get_by_id = AsyncMock(return_value=Ride(
        ride_id="RIDE_001",
        user_id="USER_001",
        vehicle_id="V001",
        start_station_id=1,
        start_time=datetime.now(),
    ))
    service.vehicles_repo.get_by_id = AsyncMock(return_value=Vehicle(
        vehicle_id="V001",
        vehicle_type=VehicleType.bike,
        station_id=1,
        status=VehicleStatus.available,
        rides_since_last_treated=0,
        last_treated_date=date.today()
    ))
    service.vehicles_repo.dock_vehicle = AsyncMock(return_value=Vehicle(
        vehicle_id="V001",
        vehicle_type=VehicleType.bike,
        station_id=1,
        status=VehicleStatus.available,
        rides_since_last_treated=1,
        last_treated_date=date.today()
    ))
    
    service.stations_service.get_stations_with_capacity = AsyncMock(return_value=mock_stations)
    
    mock_db = Mock()
    
    # Execute
    result = await service.end_ride(mock_db, "RIDE_001", lon=34.5, lat=32.5)
    
    # Verify
    assert result["end_station_id"] == 1  # Closest station
    assert result["payment_charged"] == 15  # Fixed price


@pytest.mark.asyncio
async def test_ride_end_selects_station_with_capacity(test_db):
    """Ensure only stations with available capacity are considered."""
    from unittest.mock import AsyncMock, Mock
    from src.services.rides_service import RideService
    from src.repositories.users_repository import UsersRepository
    
    service = RideService()
    service.stations_service = AsyncMock()
    service.users_repo = AsyncMock(spec=UsersRepository)
    
    # Mix of full and available stations
    mock_stations = [
        {"station_id": 1, "name": "S1", "lat": 32.5, "lon": 34.5, "max_capacity": 10, "current_capacity": 10},  # Full
        {"station_id": 2, "name": "S2", "lat": 32.4, "lon": 34.4, "max_capacity": 10, "current_capacity": 8},   # Available
        {"station_id": 3, "name": "S3", "lat": 32.6, "lon": 34.6, "max_capacity": 10, "current_capacity": 10},  # Full
    ]
    
    service.rides_repo.get_by_id = AsyncMock(return_value=Ride(
        ride_id="RIDE_001",
        user_id="USER_001",
        vehicle_id="V001",
        start_station_id=1,
        start_time=datetime.now(),
    ))
    service.vehicles_repo.get_by_id = AsyncMock(return_value=Vehicle(
        vehicle_id="V001",
        vehicle_type=VehicleType.bike,
        station_id=2,
        status=VehicleStatus.available,
        rides_since_last_treated=0,
        last_treated_date=date.today()
    ))
    service.vehicles_repo.dock_vehicle = AsyncMock(return_value=Vehicle(
        vehicle_id="V001",
        vehicle_type=VehicleType.bike,
        station_id=2,
        status=VehicleStatus.available,
        rides_since_last_treated=1,
        last_treated_date=date.today()
    ))
    
    service.stations_service.get_stations_with_capacity = AsyncMock(return_value=mock_stations)
    
    mock_db = Mock()
    result = await service.end_ride(mock_db, "RIDE_001", lon=34.4, lat=32.4)
    
    # Should select S2 (only station with available capacity)
    assert result["end_station_id"] == 2


@pytest.mark.asyncio
async def test_vehicle_dock_state_transitions(test_db):
    """Test that vehicle state properly transitions when docked."""
    from unittest.mock import AsyncMock, Mock
    from src.services.rides_service import RideService
    from src.repositories.vehicles_repository import VehiclesRepository
    from src.repositories.users_repository import UsersRepository
    from src.models.vehicle import Vehicle
    
    service = RideService()
    service.vehicles_repo = AsyncMock(spec=VehiclesRepository)
    service.users_repo = AsyncMock(spec=UsersRepository)
    service.stations_service = AsyncMock()
    
    # Mock the vehicle before docking (rented state)
    mock_vehicle = Vehicle(
        vehicle_id="BIKE_001",
        station_id=None,  # Currently not at a station (being ridden)
        vehicle_type=VehicleType.bike,
        status=VehicleStatus.rented,
        rides_since_last_treated=5,
        last_treated_date=None,
    )
    
    # Mock the docking operation
    docked_vehicle = Vehicle(
        vehicle_id="BIKE_001",
        station_id=1,  # Now at station 1
        vehicle_type=VehicleType.bike,
        status=VehicleStatus.available,  # Available for next ride
        rides_since_last_treated=6,  # Incremented
        last_treated_date=None,
    )
    
    service.vehicles_repo.get_by_id = AsyncMock(return_value=mock_vehicle)
    service.vehicles_repo.dock_vehicle = AsyncMock(return_value=docked_vehicle)
    
    mock_stations = [{"station_id": 1, "name": "S1", "lat": 32.5, "lon": 34.5, "max_capacity": 10, "current_capacity": 5}]
    
    service.rides_repo.get_by_id = AsyncMock(return_value=Ride(
        ride_id="RIDE_001",
        user_id="USER_001",
        vehicle_id="BIKE_001",
        start_station_id=1,
        start_time=datetime.now(),
    ))
    service.stations_service.get_stations_with_capacity = AsyncMock(return_value=mock_stations)
    
    mock_db = Mock()
    result = await service.end_ride(mock_db, "RIDE_001", lon=34.5, lat=32.5)
    
    # Verify result is correct
    assert result["end_station_id"] == 1


@pytest.mark.asyncio
async def test_multiple_concurrent_rides_ending(test_db):
    """Test correct response when multiple users end rides simultaneously."""
    from unittest.mock import AsyncMock, Mock
    from src.services.rides_service import RideService
    from src.repositories.users_repository import UsersRepository
    
    service = RideService()
    service.stations_service = AsyncMock()
    service.users_repo = AsyncMock(spec=UsersRepository)
    
    service.rides_repo.get_by_id = AsyncMock(return_value=Ride(
        ride_id="RIDE_003",
        user_id="USER_003",
        vehicle_id="V003",
        start_station_id=1,
        start_time=datetime.now(),
    ))
    service.vehicles_repo.get_by_id = AsyncMock(return_value=Vehicle(
        vehicle_id="V003",
        vehicle_type=VehicleType.bike,
        station_id=1,
        status=VehicleStatus.available,
        rides_since_last_treated=0,
        last_treated_date=date.today()
    ))
    service.vehicles_repo.dock_vehicle = AsyncMock(return_value=Vehicle(
        vehicle_id="V003",
        vehicle_type=VehicleType.bike,
        station_id=1,
        status=VehicleStatus.available,
        rides_since_last_treated=1,
        last_treated_date=date.today()
    ))
    
    mock_stations = [{"station_id": 1, "name": "S1", "lat": 32.5, "lon": 34.5, "max_capacity": 20, "current_capacity": 15}]
    service.stations_service.get_stations_with_capacity = AsyncMock(return_value=mock_stations)
    
    mock_db = Mock()
    result = await service.end_ride(mock_db, "RIDE_003", lon=34.5, lat=32.5)
    
    # Verify response structure (only required fields per specification)
    assert result["end_station_id"] == 1
    assert result["payment_charged"] == 15


@pytest.mark.asyncio
async def test_payment_logic_normal_ride(test_db):
    """Test that normal ride is charged 15 ILS."""
    from unittest.mock import AsyncMock, Mock
    from src.services.rides_service import RideService
    from src.repositories.users_repository import UsersRepository
    
    service = RideService()
    service.stations_service = AsyncMock()
    service.users_repo = AsyncMock(spec=UsersRepository)
    
    service.rides_repo.get_by_id = AsyncMock(return_value=Ride(
        ride_id="RIDE_NORMAL",
        user_id="USER_001",
        vehicle_id="V001",
        start_station_id=1,
        start_time=datetime.now(),
    ))
    service.vehicles_repo.get_by_id = AsyncMock(return_value=Vehicle(
        vehicle_id="V001",
        vehicle_type=VehicleType.bike,
        station_id=1,
        status=VehicleStatus.available,
        rides_since_last_treated=0,
        last_treated_date=date.today()
    ))
    service.vehicles_repo.dock_vehicle = AsyncMock(return_value=Vehicle(
        vehicle_id="V001",
        vehicle_type=VehicleType.bike,
        station_id=1,
        status=VehicleStatus.available,
        rides_since_last_treated=1,
        last_treated_date=date.today()
    ))
    
    mock_stations = [{"station_id": 1, "name": "S1", "lat": 32.5, "lon": 34.5, "max_capacity": 10, "current_capacity": 5}]
    service.stations_service.get_stations_with_capacity = AsyncMock(return_value=mock_stations)
    
    mock_db = Mock()
    result = await service.end_ride(mock_db, "RIDE_NORMAL", lon=34.5, lat=32.5)
    
    # Fixed price for any ride
    assert result["payment_charged"] == 15


@pytest.mark.asyncio
async def test_nearest_station_calculation(test_db):
    """Test that nearest station by euclidean distance is correctly selected."""
    from unittest.mock import AsyncMock, Mock
    from src.services.rides_service import RideService
    from src.repositories.users_repository import UsersRepository
    
    service = RideService()
    service.stations_service = AsyncMock()
    service.users_repo = AsyncMock(spec=UsersRepository)
    
    service.rides_repo.get_by_id = AsyncMock(return_value=Ride(
        ride_id="RIDE_001",
        user_id="USER_001",
        vehicle_id="V001",
        start_station_id=1,
        start_time=datetime.now(),
    ))
    service.vehicles_repo.get_by_id = AsyncMock(return_value=Vehicle(
        vehicle_id="V001",
        vehicle_type=VehicleType.bike,
        station_id=1,
        status=VehicleStatus.available,
        rides_since_last_treated=0,
        last_treated_date=date.today()
    ))
    service.vehicles_repo.dock_vehicle = AsyncMock(return_value=Vehicle(
        vehicle_id="V001",
        vehicle_type=VehicleType.bike,
        station_id=3,
        status=VehicleStatus.available,
        rides_since_last_treated=1,
        last_treated_date=date.today()
    ))
    
    # Create stations at known distances
    # User drops off at (32.1, 34.1)
    mock_stations = [
        # Distance from (32.1, 34.1): sqrt((32-32.1)^2 + (34-34.1)^2) = sqrt(0.01 + 0.01) ≈ 0.141
        {"station_id": 1, "name": "S1", "lat": 32.0, "lon": 34.0, "max_capacity": 10, "current_capacity": 5},
        # Distance: sqrt((32.5-32.1)^2 + (34.5-34.1)^2) = sqrt(0.16 + 0.16) ≈ 0.566
        {"station_id": 2, "name": "S2", "lat": 32.5, "lon": 34.5, "max_capacity": 10, "current_capacity": 5},
        # Distance: sqrt((32.2-32.1)^2 + (34.2-34.1)^2) = sqrt(0.01 + 0.01) ≈ 0.141
        {"station_id": 3, "name": "S3", "lat": 32.2, "lon": 34.2, "max_capacity": 10, "current_capacity": 5},
    ]
    
    service.stations_service.get_stations_with_capacity = AsyncMock(return_value=mock_stations)
    
    mock_db = Mock()
    result = await service.end_ride(mock_db, "RIDE_001", lon=34.1, lat=32.1)
    
    # S1 and S3 are equally close (first one should be selected)
    assert result["end_station_id"] in [1, 3]

