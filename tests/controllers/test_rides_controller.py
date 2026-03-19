"""Tests for RideController."""

from __future__ import annotations

import pytest
from unittest.mock import AsyncMock, Mock, patch
from datetime import datetime
from fastapi import HTTPException

from src.schemas.ride_schemas import RideStartRequest
from src.models.ride import Ride


@pytest.mark.asyncio
async def test_start_ride_success():
    """Test successfully starting a ride."""
    # Import the endpoint function directly
    from src.controllers.ride_controller import start_ride

    # Create mock request
    request = RideStartRequest(user_id="USER001", lon=34.0, lat=32.0)

    # Create mock database
    mock_db = Mock()

    # Create mock ride response
    expected_ride = Ride(
        ride_id="RIDE001",
        user_id="USER001",
        vehicle_id="V001",
        start_station_id=1,
        start_time=datetime(2026, 3, 17, 10, 0),
        is_degraded_report=False
    )

    # We need to patch the RideService within the controller
    with patch('src.controllers.ride_controller.service') as mock_service:
        mock_service.start_new_ride = AsyncMock(return_value=expected_ride)

        # Call the endpoint
        result = await start_ride(request, mock_db)

        # Assertions
        assert result.ride_id == "RIDE001"
        assert result.user_id == "USER001"
        assert result.vehicle_id == "V001"
        assert result.start_station_id == 1


@pytest.mark.asyncio
async def test_start_ride_no_vehicles_available():
    """Test starting a ride when no vehicles are available."""
    from src.controllers.ride_controller import start_ride

    request = RideStartRequest(user_id="USER001", lon=34.0, lat=32.0)
    mock_db = Mock()

    with patch('src.controllers.ride_controller.service') as mock_service:
        # Service raises HTTPException(404) when no vehicles are available
        mock_service.start_new_ride = AsyncMock(
            side_effect=HTTPException(status_code=404, detail="Could not start ride.")
        )

        # The controller should propagate the HTTPException unchanged
        with pytest.raises(HTTPException) as exc_info:
            await start_ride(request, mock_db)

        # Expect the original 404 status and detail from the service
        assert exc_info.value.status_code == 404
        assert exc_info.value.detail == "Could not start ride."


@pytest.mark.asyncio
async def test_start_ride_service_error():
    """Test handling of service errors."""
    from src.controllers.ride_controller import start_ride
    from src.exceptions import ValidationException

    request = RideStartRequest(user_id="USER001", lon=34.0, lat=32.0)
    mock_db = Mock()

    with patch('src.controllers.ride_controller.service') as mock_service:
        mock_service.start_new_ride = AsyncMock(
            side_effect=ValidationException("Invalid input")
        )

        # Should raise ValidationException (global handler will convert to 400)
        with pytest.raises(ValidationException) as exc_info:
            await start_ride(request, mock_db)

        assert "Invalid input" in str(exc_info.value.message)


@pytest.mark.asyncio
async def test_start_ride_unexpected_error():
    """Test handling of unexpected server errors."""
    from src.controllers.ride_controller import start_ride

    request = RideStartRequest(user_id="USER001", lon=34.0, lat=32.0)
    mock_db = Mock()

    with patch('src.controllers.ride_controller.service') as mock_service:
        mock_service.start_new_ride = AsyncMock(
            side_effect=RuntimeError("Database connection failed")
        )

        # Should raise RuntimeError (FastAPI will handle as 500)
        with pytest.raises(RuntimeError) as exc_info:
            await start_ride(request, mock_db)

        assert "Database connection failed" in str(exc_info.value)


@pytest.mark.asyncio
async def test_start_ride_returns_ride_model():
    """Test that start_ride returns a valid Ride model."""
    from src.controllers.ride_controller import start_ride

    request = RideStartRequest(user_id="USER_MODEL", lon=34.5, lat=32.5)
    mock_db = Mock()

    expected_ride = Ride(
        ride_id="RIDE_MODEL_TEST",
        user_id="USER_MODEL",
        vehicle_id="V_MODEL",
        start_station_id=3,
        start_time=datetime(2026, 3, 17, 12, 0),
        is_degraded_report=False
    )

    with patch('src.controllers.ride_controller.service') as mock_service:
        mock_service.start_new_ride = AsyncMock(return_value=expected_ride)

        result = await start_ride(request, mock_db)

        # Verify it's a valid Ride instance
        assert isinstance(result, Ride)
        assert result.ride_id == "RIDE_MODEL_TEST"
        assert result.start_station_id == 3


@pytest.mark.asyncio
async def test_start_ride_none_return():
    """Test handling when service returns None."""
    from src.controllers.ride_controller import start_ride

    request = RideStartRequest(user_id="USER001", lon=34.0, lat=32.0)
    mock_db = Mock()

    with patch('src.controllers.ride_controller.service') as mock_service:
        # Service now returns a ride, not None (removed the None check from controller)
        mock_service.start_new_ride = AsyncMock(return_value=None)

        # This will return None (controller no longer checks for None)
        result = await start_ride(request, mock_db)
        assert result is None


