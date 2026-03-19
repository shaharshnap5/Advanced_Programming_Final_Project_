"""Tests for RideService."""

from __future__ import annotations

import pytest
from unittest.mock import AsyncMock, Mock, patch
from datetime import datetime, date
from fastapi import HTTPException

from src.services.rides_service import RideService
from src.repositories.vehicles_repository import VehiclesRepository
from src.repositories.rides_repository import RidesRepository
from src.services.stations_service import StationsService
from src.models.ride import Ride
from src.models.station import Station
from src.models.vehicle import Vehicle, VehicleType, VehicleStatus


@pytest.mark.asyncio
async def test_start_new_ride_success():
    """Test successfully starting a new ride."""
    # Mock the service dependencies
    mock_stations_service = Mock(spec=StationsService)
    mock_vehicles_repo = Mock(spec=VehiclesRepository)
    mock_rides_repo = Mock(spec=RidesRepository)

    # Setup mock returns
    mock_stations_service.get_nearest_station_with_vehicles = AsyncMock(
        return_value=Station(station_id=1, name="Station 1", lat=32.0, lon=34.0, max_capacity=10)
    )

    mock_vehicles_repo.get_available_vehicles_by_station = AsyncMock(
        return_value=[
            Vehicle(
                vehicle_id="V001",
                vehicle_type=VehicleType.bike,
                station_id=1,
                status=VehicleStatus.available,
                rides_since_last_treated=0,
                last_treated_date=date.today()
            )
        ]
    )

    mock_vehicles_repo.mark_vehicle_as_rented = AsyncMock()
    mock_rides_repo.create_active_ride = AsyncMock()
    mock_rides_repo.get_active_ride_by_user = AsyncMock(return_value=None)

    # Create service with mocked dependencies
    service = RideService()
    service.stations_service = mock_stations_service
    service.vehicles_repo = mock_vehicles_repo
    service.rides_repo = mock_rides_repo

    mock_db = Mock()

    # Call the service
    result = await service.start_new_ride(mock_db, user_id="USER001", lon=34.0, lat=32.0)

    # Assertions
    assert isinstance(result, Ride)
    assert result.user_id == "USER001"
    assert result.vehicle_id == "V001"
    assert result.start_station_id == 1
    assert result.start_time is not None
    assert result.is_degraded_report is False

    # Verify method calls
    mock_stations_service.get_nearest_station_with_vehicles.assert_called_once()
    mock_vehicles_repo.mark_vehicle_as_rented.assert_called_once_with(mock_db, "V001")
    mock_rides_repo.create_active_ride.assert_called_once()


@pytest.mark.asyncio
async def test_start_new_ride_no_available_station():
    """Test starting a ride when no stations have vehicles."""
    mock_stations_service = Mock(spec=StationsService)
    mock_vehicles_repo = Mock(spec=VehiclesRepository)
    mock_rides_repo = Mock(spec=RidesRepository)

    # Station service returns None
    mock_stations_service.get_nearest_station_with_vehicles = AsyncMock(return_value=None)
    mock_rides_repo.get_active_ride_by_user = AsyncMock(return_value=None)

    service = RideService()
    service.stations_service = mock_stations_service
    service.vehicles_repo = mock_vehicles_repo
    service.rides_repo = mock_rides_repo

    mock_db = Mock()

    # Should raise HTTPException
    with pytest.raises(HTTPException) as exc_info:
        await service.start_new_ride(mock_db, user_id="USER001", lon=34.0, lat=32.0)

    assert exc_info.value.status_code == 404
    assert "No available vehicles found" in exc_info.value.detail


@pytest.mark.asyncio
async def test_start_new_ride_vehicle_type_priority_scooter():
    """Test that scooters are prioritized over other vehicle types."""
    mock_stations_service = Mock(spec=StationsService)
    mock_vehicles_repo = Mock(spec=VehiclesRepository)
    mock_rides_repo = Mock(spec=RidesRepository)

    mock_stations_service.get_nearest_station_with_vehicles = AsyncMock(
        return_value=Station(station_id=1, name="Station 1", lat=32.0, lon=34.0, max_capacity=10)
    )

    # Return multiple vehicles with different types
    mock_vehicles_repo.get_available_vehicles_by_station = AsyncMock(
        return_value=[
            Vehicle(vehicle_id="V001", vehicle_type=VehicleType.bike, station_id=1, status=VehicleStatus.available, rides_since_last_treated=0, last_treated_date=date.today()),
            Vehicle(vehicle_id="V002", vehicle_type=VehicleType.scooter, station_id=1, status=VehicleStatus.available, rides_since_last_treated=0, last_treated_date=date.today()),
            Vehicle(vehicle_id="V003", vehicle_type=VehicleType.ebike, station_id=1, status=VehicleStatus.available, rides_since_last_treated=0, last_treated_date=date.today()),
        ]
    )

    mock_vehicles_repo.mark_vehicle_as_rented = AsyncMock()
    mock_rides_repo.create_active_ride = AsyncMock()
    mock_rides_repo.get_active_ride_by_user = AsyncMock(return_value=None)

    service = RideService()
    service.stations_service = mock_stations_service
    service.vehicles_repo = mock_vehicles_repo
    service.rides_repo = mock_rides_repo

    mock_db = Mock()

    result = await service.start_new_ride(mock_db, user_id="USER001", lon=34.0, lat=32.0)

    # Scooter should be selected
    assert result.vehicle_id == "V002"
    mock_vehicles_repo.mark_vehicle_as_rented.assert_called_with(mock_db, "V002")


@pytest.mark.asyncio
async def test_start_new_ride_vehicle_type_priority_ebike():
    """Test that e-bikes are prioritized over bicycles."""
    mock_stations_service = Mock(spec=StationsService)
    mock_vehicles_repo = Mock(spec=VehiclesRepository)
    mock_rides_repo = Mock(spec=RidesRepository)

    mock_stations_service.get_nearest_station_with_vehicles = AsyncMock(
        return_value=Station(station_id=1, name="Station 1", lat=32.0, lon=34.0, max_capacity=10)
    )

    # Return bikes and e-bikes (no scooters)
    mock_vehicles_repo.get_available_vehicles_by_station = AsyncMock(
        return_value=[
            Vehicle(vehicle_id="V001", vehicle_type=VehicleType.bike, station_id=1, status=VehicleStatus.available, rides_since_last_treated=0, last_treated_date=date.today()),
            Vehicle(vehicle_id="V003", vehicle_type=VehicleType.ebike, station_id=1, status=VehicleStatus.available, rides_since_last_treated=0, last_treated_date=date.today()),
        ]
    )

    mock_vehicles_repo.mark_vehicle_as_rented = AsyncMock()
    mock_rides_repo.create_active_ride = AsyncMock()
    mock_rides_repo.get_active_ride_by_user = AsyncMock(return_value=None)

    service = RideService()
    service.stations_service = mock_stations_service
    service.vehicles_repo = mock_vehicles_repo
    service.rides_repo = mock_rides_repo

    mock_db = Mock()

    result = await service.start_new_ride(mock_db, user_id="USER001", lon=34.0, lat=32.0)

    # E-bike should be selected
    assert result.vehicle_id == "V003"


@pytest.mark.asyncio
async def test_start_new_ride_vehicle_id_sorting():
    """Test that vehicles of same type are sorted by ID."""
    mock_stations_service = Mock(spec=StationsService)
    mock_vehicles_repo = Mock(spec=VehiclesRepository)
    mock_rides_repo = Mock(spec=RidesRepository)

    mock_stations_service.get_nearest_station_with_vehicles = AsyncMock(
        return_value=Station(station_id=1, name="Station 1", lat=32.0, lon=34.0, max_capacity=10)
    )

    # Return multiple scooters
    mock_vehicles_repo.get_available_vehicles_by_station = AsyncMock(
        return_value=[
            Vehicle(vehicle_id="SCOOTER003", vehicle_type=VehicleType.scooter, station_id=1, status=VehicleStatus.available, rides_since_last_treated=0, last_treated_date=date.today()),
            Vehicle(vehicle_id="SCOOTER001", vehicle_type=VehicleType.scooter, station_id=1, status=VehicleStatus.available, rides_since_last_treated=0, last_treated_date=date.today()),
            Vehicle(vehicle_id="SCOOTER002", vehicle_type=VehicleType.scooter, station_id=1, status=VehicleStatus.available, rides_since_last_treated=0, last_treated_date=date.today()),
        ]
    )

    mock_vehicles_repo.mark_vehicle_as_rented = AsyncMock()
    mock_rides_repo.create_active_ride = AsyncMock()
    mock_rides_repo.get_active_ride_by_user = AsyncMock(return_value=None)

    service = RideService()
    service.stations_service = mock_stations_service
    service.vehicles_repo = mock_vehicles_repo
    service.rides_repo = mock_rides_repo

    mock_db = Mock()

    result = await service.start_new_ride(mock_db, user_id="USER001", lon=34.0, lat=32.0)

    # Should pick the scooter with the lowest ID
    assert result.vehicle_id == "SCOOTER001"


@pytest.mark.asyncio
async def test_start_new_ride_returns_correct_model():
    """Test that start_new_ride returns a valid Ride model."""
    mock_stations_service = Mock(spec=StationsService)
    mock_vehicles_repo = Mock(spec=VehiclesRepository)
    mock_rides_repo = Mock(spec=RidesRepository)

    mock_stations_service.get_nearest_station_with_vehicles = AsyncMock(
        return_value=Station(station_id=5, name="Station 5", lat=32.5, lon=34.5, max_capacity=10)
    )

    mock_vehicles_repo.get_available_vehicles_by_station = AsyncMock(
        return_value=[
            Vehicle(vehicle_id="V_TEST", vehicle_type=VehicleType.bike, station_id=5, status=VehicleStatus.available, rides_since_last_treated=0, last_treated_date=date.today())
        ]
    )

    mock_vehicles_repo.mark_vehicle_as_rented = AsyncMock()
    mock_rides_repo.create_active_ride = AsyncMock()
    mock_rides_repo.get_active_ride_by_user = AsyncMock(return_value=None)

    service = RideService()
    service.stations_service = mock_stations_service
    service.vehicles_repo = mock_vehicles_repo
    service.rides_repo = mock_rides_repo

    mock_db = Mock()

    result = await service.start_new_ride(mock_db, user_id="USER_TEST", lon=34.5, lat=32.5)

    # Verify Ride model structure
    assert hasattr(result, 'ride_id')
    assert hasattr(result, 'user_id')
    assert hasattr(result, 'vehicle_id')
    assert hasattr(result, 'start_station_id')
    assert hasattr(result, 'start_time')
    assert hasattr(result, 'is_degraded_report')

    # Verify model values
    assert result.user_id == "USER_TEST"
    assert result.vehicle_id == "V_TEST"
    assert result.start_station_id == 5
    assert result.is_degraded_report is False


@pytest.mark.asyncio
async def test_start_new_ride_creates_database_entry():
    """Test that start_new_ride calls create_active_ride with correct parameters."""
    mock_stations_service = Mock(spec=StationsService)
    mock_vehicles_repo = Mock(spec=VehiclesRepository)
    mock_rides_repo = Mock(spec=RidesRepository)

    mock_stations_service.get_nearest_station_with_vehicles = AsyncMock(
        return_value=Station(station_id=2, name="Station 2", lat=32.0, lon=34.0, max_capacity=10)
    )

    mock_vehicles_repo.get_available_vehicles_by_station = AsyncMock(
        return_value=[
            Vehicle(vehicle_id="V_NEW", vehicle_type=VehicleType.bike, station_id=2, status=VehicleStatus.available, rides_since_last_treated=0, last_treated_date=date.today())
        ]
    )

    mock_vehicles_repo.mark_vehicle_as_rented = AsyncMock()
    mock_rides_repo.create_active_ride = AsyncMock()
    mock_rides_repo.get_active_ride_by_user = AsyncMock(return_value=None)

    service = RideService()
    service.stations_service = mock_stations_service
    service.vehicles_repo = mock_vehicles_repo
    service.rides_repo = mock_rides_repo

    mock_db = Mock()

    result = await service.start_new_ride(mock_db, user_id="USER_NEW", lon=34.0, lat=32.0)

    # Verify create_active_ride was called with correct parameters
    assert mock_rides_repo.create_active_ride.called
    # Get the positional and keyword arguments
    call_args = mock_rides_repo.create_active_ride.call_args
    args, kwargs = call_args

    # Verify positional arguments
    assert args[1] == result.ride_id  # ride_id
    assert args[2] == "USER_NEW"  # user_id
    assert args[3] == "V_NEW"  # vehicle_id
    assert args[4] == 2  # start_station_id


@pytest.mark.asyncio
async def test_start_new_ride_user_already_has_active_ride():
    """Test that a user cannot start a new ride if they already have an active one."""
    mock_stations_service = Mock(spec=StationsService)
    mock_vehicles_repo = Mock(spec=VehiclesRepository)
    mock_rides_repo = Mock(spec=RidesRepository)

    # Mock return an active ride for the user
    existing_ride = Ride(
        ride_id="EXISTING_RIDE",
        user_id="USER_WITH_ACTIVE_RIDE",
        vehicle_id="V001",
        start_station_id=1,
        start_time=datetime(2026, 3, 19, 10, 0, 0),
        end_time=None,
        is_degraded_report=False
    )
    mock_rides_repo.get_active_ride_by_user = AsyncMock(return_value=existing_ride)

    service = RideService()
    service.stations_service = mock_stations_service
    service.vehicles_repo = mock_vehicles_repo
    service.rides_repo = mock_rides_repo

    mock_db = Mock()

    # Should raise HTTPException with status code 409
    with pytest.raises(HTTPException) as exc_info:
        await service.start_new_ride(mock_db, user_id="USER_WITH_ACTIVE_RIDE", lon=34.0, lat=32.0)

    assert exc_info.value.status_code == 409
    assert "already has an active ride" in exc_info.value.detail

    # Verify that station service was never called (early exit)
    mock_stations_service.get_nearest_station_with_vehicles.assert_not_called()
    # Verify that vehicles repo was never called
    mock_vehicles_repo.get_available_vehicles_by_station.assert_not_called()
    # Verify that a new ride was not created
    mock_rides_repo.create_active_ride.assert_not_called()

