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
async def test_start_new_ride_vehicle_type_priority_bicycle():
    """Test that bicycles are prioritized over other vehicle types."""
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

    service = RideService()
    service.stations_service = mock_stations_service
    service.vehicles_repo = mock_vehicles_repo
    service.rides_repo = mock_rides_repo

    mock_db = Mock()

    result = await service.start_new_ride(mock_db, user_id="USER001", lon=34.0, lat=32.0)

    # Bicycle should be selected
    assert result.vehicle_id == "V001"
    mock_vehicles_repo.mark_vehicle_as_rented.assert_called_with(mock_db, "V001")


@pytest.mark.asyncio
async def test_start_new_ride_vehicle_type_priority_ebike():
    """Test that bicycles are prioritized over e-bikes."""
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

    service = RideService()
    service.stations_service = mock_stations_service
    service.vehicles_repo = mock_vehicles_repo
    service.rides_repo = mock_rides_repo

    mock_db = Mock()

    result = await service.start_new_ride(mock_db, user_id="USER001", lon=34.0, lat=32.0)

    # Bicycle should be selected (prioritized over e-bike)
    assert result.vehicle_id == "V001"


@pytest.mark.asyncio
async def test_start_new_ride_vehicle_id_sorting():
    """Test that vehicles of same type are sorted by ID."""
    mock_stations_service = Mock(spec=StationsService)
    mock_vehicles_repo = Mock(spec=VehiclesRepository)
    mock_rides_repo = Mock(spec=RidesRepository)

    mock_stations_service.get_nearest_station_with_vehicles = AsyncMock(
        return_value=Station(station_id=1, name="Station 1", lat=32.0, lon=34.0, max_capacity=10)
    )

    # Return multiple bicycles
    mock_vehicles_repo.get_available_vehicles_by_station = AsyncMock(
        return_value=[
            Vehicle(vehicle_id="BIKE003", vehicle_type=VehicleType.bike, station_id=1, status=VehicleStatus.available, rides_since_last_treated=0, last_treated_date=date.today()),
            Vehicle(vehicle_id="BIKE001", vehicle_type=VehicleType.bike, station_id=1, status=VehicleStatus.available, rides_since_last_treated=0, last_treated_date=date.today()),
            Vehicle(vehicle_id="BIKE002", vehicle_type=VehicleType.bike, station_id=1, status=VehicleStatus.available, rides_since_last_treated=0, last_treated_date=date.today()),
        ]
    )

    mock_vehicles_repo.mark_vehicle_as_rented = AsyncMock()
    mock_rides_repo.create_active_ride = AsyncMock()

    service = RideService()
    service.stations_service = mock_stations_service
    service.vehicles_repo = mock_vehicles_repo
    service.rides_repo = mock_rides_repo

    mock_db = Mock()

    result = await service.start_new_ride(mock_db, user_id="USER001", lon=34.0, lat=32.0)

    # Should pick the bicycle with the lowest ID
    assert result.vehicle_id == "BIKE001"


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

