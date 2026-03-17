from __future__ import annotations

import pytest
from unittest.mock import AsyncMock, Mock, patch

from src.services.rides_service import RidesService
from src.services.stations_service import StationsService
from src.services.users_service import UsersService
from src.services.vehicles_service import VehiclesService
from src.models.ride import Ride
from src.models.station import Station
from fastapi import HTTPException


@pytest.mark.asyncio
async def test_end_ride_success():
    """Test successful ride end with all steps (dock, charge, clear active ride)."""
    # Mock services
    mock_stations_service = AsyncMock(spec=StationsService)
    mock_users_service = AsyncMock(spec=UsersService)
    mock_vehicles_service = AsyncMock(spec=VehiclesService)

    from src.models.station import Station

    # Mock station with capacity (returned as Station object)
    mock_station = Station(
        station_id=1,
        name="Test Station",
        lat=32.5,
        lon=34.5,
        max_capacity=10,
        vehicles=[],
    )
    mock_stations_service.get_nearest_station_with_capacity = AsyncMock(
        return_value=mock_station
    )

    # Mock vehicle
    mock_vehicle = {
        "vehicle_id": "VEH001",
        "station_id": None,
        "vehicle_type": "bike",
        "status": "rented",
        "rides_since_last_treated": 5,
        "last_treated_date": None,
    }
    mock_vehicles_service.get_vehicle_by_id = AsyncMock(return_value=mock_vehicle)
    mock_vehicles_service.dock_vehicle = AsyncMock(return_value=mock_vehicle)

    # Mock user
    mock_user = {
        "user_id": "USER001",
        "payment_token": "tok_test",
        "current_ride_id": "RIDE001",
    }
    mock_users_service.get_user_by_id = AsyncMock(return_value=mock_user)
    mock_users_service.clear_current_ride = AsyncMock(return_value=True)

    service = RidesService(
        stations_service=mock_stations_service,
        users_service=mock_users_service,
        vehicles_service=mock_vehicles_service,
    )

    # Mock FleetManager
    from src.models.FleetManager import FleetManager

    with patch.object(FleetManager, "_instance", None):
        fm = FleetManager()
        ride = Ride(ride_id="RIDE001", user_id="USER001", vehicle_id="VEH001")
        fm.active_rides["RIDE001"] = ride

        mock_db = Mock()

        result = await service.end_ride(mock_db, "RIDE001", 34.5, 32.5)

        assert result["end_station_id"] == 1
        assert result["end_station"].station_id == 1
        assert result["active_users"] == []

        mock_stations_service.get_nearest_station_with_capacity.assert_called_once()
        mock_vehicles_service.get_vehicle_by_id.assert_called_once_with(
            mock_db, "VEH001"
        )
        mock_vehicles_service.dock_vehicle.assert_called_once()
        mock_users_service.get_user_by_id.assert_called_once_with(mock_db, "USER001")
        mock_users_service.clear_current_ride.assert_called_once_with(mock_db, "USER001")


@pytest.mark.asyncio
async def test_end_ride_not_found():
    """Test error when ride_id does not exist in active rides."""
    service = RidesService()

    from src.models.FleetManager import FleetManager

    with patch.object(FleetManager, "_instance", None):
        fm = FleetManager()
        # Don't add any rides to active_rides
        mock_db = Mock()

        with pytest.raises(HTTPException) as exc_info:
            await service.end_ride(mock_db, "NONEXISTENT", 34.5, 32.5)

        assert exc_info.value.status_code == 404
        assert "not found" in exc_info.value.detail.lower()


@pytest.mark.asyncio
async def test_end_ride_no_available_station():
    """Test error when no station with free capacity is available."""
    mock_stations_service = AsyncMock(spec=StationsService)
    mock_users_service = AsyncMock(spec=UsersService)
    mock_vehicles_service = AsyncMock(spec=VehiclesService)

    # No available stations
    mock_stations_service.get_nearest_station_with_capacity = AsyncMock(
        return_value=None
    )

    service = RidesService(
        stations_service=mock_stations_service,
        users_service=mock_users_service,
        vehicles_service=mock_vehicles_service,
    )

    from src.models.FleetManager import FleetManager

    with patch.object(FleetManager, "_instance", None):
        fm = FleetManager()
        ride = Ride(ride_id="RIDE001", user_id="USER001", vehicle_id="VEH001")
        fm.active_rides["RIDE001"] = ride

        mock_db = Mock()

        with pytest.raises(HTTPException) as exc_info:
            await service.end_ride(mock_db, "RIDE001", 34.5, 32.5)

        assert exc_info.value.status_code == 400
        assert "station" in exc_info.value.detail.lower()


@pytest.mark.asyncio
async def test_end_ride_vehicle_not_found():
    """Test error when vehicle does not exist in database."""
    mock_stations_service = AsyncMock(spec=StationsService)
    mock_users_service = AsyncMock(spec=UsersService)
    mock_vehicles_service = AsyncMock(spec=VehiclesService)

    from src.models.station import Station

    mock_station = Station(
        station_id=1,
        name="Test Station",
        lat=32.5,
        lon=34.5,
        max_capacity=10,
        vehicles=[],
    )
    mock_stations_service.get_nearest_station_with_capacity = AsyncMock(
        return_value=mock_station
    )

    # Vehicle not found
    mock_vehicles_service.get_vehicle_by_id = AsyncMock(return_value=None)

    service = RidesService(
        stations_service=mock_stations_service,
        users_service=mock_users_service,
        vehicles_service=mock_vehicles_service,
    )

    from src.models.FleetManager import FleetManager

    with patch.object(FleetManager, "_instance", None):
        fm = FleetManager()
        ride = Ride(ride_id="RIDE001", user_id="USER001", vehicle_id="VEH001")
        fm.active_rides["RIDE001"] = ride

        mock_db = Mock()

        with pytest.raises(HTTPException) as exc_info:
            await service.end_ride(mock_db, "RIDE001", 34.5, 32.5)

        assert exc_info.value.status_code == 404
        assert "Vehicle" in exc_info.value.detail


@pytest.mark.asyncio
async def test_end_ride_user_not_found():
    """Test error when user does not exist in database."""
    mock_stations_service = AsyncMock(spec=StationsService)
    mock_users_service = AsyncMock(spec=UsersService)
    mock_vehicles_service = AsyncMock(spec=VehiclesService)

    from src.models.station import Station

    mock_station = Station(
        station_id=1,
        name="Test Station",
        lat=32.5,
        lon=34.5,
        max_capacity=10,
        vehicles=[],
    )
    mock_stations_service.get_nearest_station_with_capacity = AsyncMock(
        return_value=mock_station
    )

    mock_vehicle = {
        "vehicle_id": "VEH001",
        "station_id": None,
        "vehicle_type": "bike",
        "status": "rented",
        "rides_since_last_treated": 5,
        "last_treated_date": None,
    }
    mock_vehicles_service.get_vehicle_by_id = AsyncMock(return_value=mock_vehicle)

    # User not found
    mock_users_service.get_user_by_id = AsyncMock(return_value=None)

    service = RidesService(
        stations_service=mock_stations_service,
        users_service=mock_users_service,
        vehicles_service=mock_vehicles_service,
    )

    from src.models.FleetManager import FleetManager

    with patch.object(FleetManager, "_instance", None):
        fm = FleetManager()
        ride = Ride(ride_id="RIDE001", user_id="USER001", vehicle_id="VEH001")
        fm.active_rides["RIDE001"] = ride

        mock_db = Mock()

        with pytest.raises(HTTPException) as exc_info:
            await service.end_ride(mock_db, "RIDE001", 34.5, 32.5)

        assert exc_info.value.status_code == 404
        assert "User" in exc_info.value.detail


@pytest.mark.asyncio
async def test_end_ride_increments_rides_counter():
    """Test that rides_since_last_treated is incremented correctly."""
    mock_stations_service = AsyncMock(spec=StationsService)
    mock_users_service = AsyncMock(spec=UsersService)
    mock_vehicles_service = AsyncMock(spec=VehiclesService)

    from src.models.station import Station

    mock_station = Station(
        station_id=1,
        name="Test Station",
        lat=32.5,
        lon=34.5,
        max_capacity=10,
        vehicles=[],
    )
    mock_stations_service.get_nearest_station_with_capacity = AsyncMock(
        return_value=mock_station
    )

    mock_vehicle = {
        "vehicle_id": "VEH001",
        "station_id": None,
        "vehicle_type": "bike",
        "status": "rented",
        "rides_since_last_treated": 5,
        "last_treated_date": None,
    }
    mock_vehicles_service.get_vehicle_by_id = AsyncMock(return_value=mock_vehicle)
    mock_vehicles_service.dock_vehicle = AsyncMock(return_value=mock_vehicle)

    mock_user = {"user_id": "USER001", "payment_token": "tok_test"}
    mock_users_service.get_user_by_id = AsyncMock(return_value=mock_user)
    mock_users_service.clear_current_ride = AsyncMock(return_value=True)

    service = RidesService(
        stations_service=mock_stations_service,
        users_service=mock_users_service,
        vehicles_service=mock_vehicles_service,
    )

    from src.models.FleetManager import FleetManager

    with patch.object(FleetManager, "_instance", None):
        fm = FleetManager()
        ride = Ride(ride_id="RIDE001", user_id="USER001", vehicle_id="VEH001")
        fm.active_rides["RIDE001"] = ride

        mock_db = Mock()
        await service.end_ride(mock_db, "RIDE001", 34.5, 32.5)

        # Verify dock_vehicle was called with incremented rides (5 + 1 = 6)
        mock_vehicles_service.dock_vehicle.assert_called_once()
        call_args = mock_vehicles_service.dock_vehicle.call_args
        assert call_args[0][2] == 1  # station_id
        assert call_args[0][3] == 6  # rides_since_last_treated (5 + 1)


@pytest.mark.asyncio
async def test_end_ride_vehicle_becomes_degraded_after_10_rides():
    """Test that vehicle status becomes 'degraded' when rides exceed 10."""
    mock_stations_service = AsyncMock(spec=StationsService)
    mock_users_service = AsyncMock(spec=UsersService)
    mock_vehicles_service = AsyncMock(spec=VehiclesService)

    from src.models.station import Station

    mock_station = Station(
        station_id=1,
        name="Test Station",
        lat=32.5,
        lon=34.5,
        max_capacity=10,
        vehicles=[],
    )
    mock_stations_service.get_nearest_station_with_capacity = AsyncMock(
        return_value=mock_station
    )

    # Vehicle with 10 rides (will become 11 after this ride)
    mock_vehicle = {
        "vehicle_id": "VEH001",
        "station_id": None,
        "vehicle_type": "bike",
        "status": "rented",
        "rides_since_last_treated": 10,
        "last_treated_date": None,
    }
    mock_vehicles_service.get_vehicle_by_id = AsyncMock(return_value=mock_vehicle)
    mock_vehicles_service.dock_vehicle = AsyncMock(return_value=mock_vehicle)

    mock_user = {"user_id": "USER001", "payment_token": "tok_test"}
    mock_users_service.get_user_by_id = AsyncMock(return_value=mock_user)
    mock_users_service.clear_current_ride = AsyncMock(return_value=True)

    service = RidesService(
        stations_service=mock_stations_service,
        users_service=mock_users_service,
        vehicles_service=mock_vehicles_service,
    )

    from src.models.FleetManager import FleetManager

    with patch.object(FleetManager, "_instance", None):
        fm = FleetManager()
        ride = Ride(ride_id="RIDE001", user_id="USER001", vehicle_id="VEH001")
        fm.active_rides["RIDE001"] = ride

        mock_db = Mock()
        await service.end_ride(mock_db, "RIDE001", 34.5, 32.5)

        # Verify dock_vehicle was called with status='degraded'
        mock_vehicles_service.dock_vehicle.assert_called_once()
        call_args = mock_vehicles_service.dock_vehicle.call_args
        assert call_args[0][4] == "degraded"  # status


@pytest.mark.asyncio
async def test_end_ride_charges_correctly():
    """Test that user is charged with the correct amount (15 ILS)."""
    mock_stations_service = AsyncMock(spec=StationsService)
    mock_users_service = AsyncMock(spec=UsersService)
    mock_vehicles_service = AsyncMock(spec=VehiclesService)

    from src.models.station import Station

    mock_station = Station(
        station_id=1,
        name="Test Station",
        lat=32.5,
        lon=34.5,
        max_capacity=10,
        vehicles=[],
    )
    mock_stations_service.get_nearest_station_with_capacity = AsyncMock(
        return_value=mock_station
    )

    mock_vehicle = {
        "vehicle_id": "VEH001",
        "station_id": None,
        "vehicle_type": "bike",
        "status": "rented",
        "rides_since_last_treated": 5,
        "last_treated_date": None,
    }
    mock_vehicles_service.get_vehicle_by_id = AsyncMock(return_value=mock_vehicle)
    mock_vehicles_service.dock_vehicle = AsyncMock(return_value=mock_vehicle)

    mock_user = {"user_id": "USER001", "payment_token": "tok_test"}
    mock_users_service.get_user_by_id = AsyncMock(return_value=mock_user)
    mock_users_service.clear_current_ride = AsyncMock(return_value=True)

    service = RidesService(
        stations_service=mock_stations_service,
        users_service=mock_users_service,
        vehicles_service=mock_vehicles_service,
    )

    from src.models.FleetManager import FleetManager

    with patch.object(FleetManager, "_instance", None):
        fm = FleetManager()
        ride = Ride(ride_id="RIDE001", user_id="USER001", vehicle_id="VEH001", is_degraded_report=False)
        fm.active_rides["RIDE001"] = ride

        mock_db = Mock()
        result = await service.end_ride(mock_db, "RIDE001", 34.5, 32.5)

        assert result["payment_charged"] == 15  # Fixed 15 ILS


@pytest.mark.asyncio
async def test_end_ride_free_when_degraded():
    """Test that degraded ride reports charge 0 ILS."""
    mock_stations_service = AsyncMock(spec=StationsService)
    mock_users_service = AsyncMock(spec=UsersService)
    mock_vehicles_service = AsyncMock(spec=VehiclesService)

    from src.models.station import Station

    mock_station = Station(
        station_id=1,
        name="Test Station",
        lat=32.5,
        lon=34.5,
        max_capacity=10,
        vehicles=[],
    )
    mock_stations_service.get_nearest_station_with_capacity = AsyncMock(
        return_value=mock_station
    )

    mock_vehicle = {
        "vehicle_id": "VEH001",
        "station_id": None,
        "vehicle_type": "bike",
        "status": "rented",
        "rides_since_last_treated": 5,
        "last_treated_date": None,
    }
    mock_vehicles_service.get_vehicle_by_id = AsyncMock(return_value=mock_vehicle)
    mock_vehicles_service.dock_vehicle = AsyncMock(return_value=mock_vehicle)

    mock_user = {"user_id": "USER001", "payment_token": "tok_test"}
    mock_users_service.get_user_by_id = AsyncMock(return_value=mock_user)
    mock_users_service.clear_current_ride = AsyncMock(return_value=True)

    service = RidesService(
        stations_service=mock_stations_service,
        users_service=mock_users_service,
        vehicles_service=mock_vehicles_service,
    )

    from src.models.FleetManager import FleetManager

    with patch.object(FleetManager, "_instance", None):
        fm = FleetManager()
        ride = Ride(ride_id="RIDE001", user_id="USER001", vehicle_id="VEH001", is_degraded_report=True)
        fm.active_rides["RIDE001"] = ride

        mock_db = Mock()
        result = await service.end_ride(mock_db, "RIDE001", 34.5, 32.5)

        assert result["payment_charged"] == 0  # Free ride for degraded report
