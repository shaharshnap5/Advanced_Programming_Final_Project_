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

    request = RideStartRequest(user_id="USER001", lon=34.0, lat=32.0)
    mock_db = Mock()

    with patch('src.controllers.ride_controller.service') as mock_service:
        mock_service.start_new_ride = AsyncMock(
            side_effect=ValueError("User not found")
        )

        # Should raise HTTPException with 400 status
        with pytest.raises(HTTPException) as exc_info:
            await start_ride(request, mock_db)

        assert exc_info.value.status_code == 400
        assert "User not found" in str(exc_info.value.detail)


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

        # Should raise HTTPException with 500 status
        with pytest.raises(HTTPException) as exc_info:
            await start_ride(request, mock_db)

        assert exc_info.value.status_code == 500


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
        mock_service.start_new_ride = AsyncMock(return_value=None)

        # Should raise HTTPException
        with pytest.raises(HTTPException) as exc_info:
            await start_ride(request, mock_db)

        # 404 is correct when ride could not be started (not found)
        assert exc_info.value.status_code == 404
        assert "Could not start ride" in exc_info.value.detail


@pytest.mark.asyncio
async def test_get_active_users_via_api():
    from httpx import AsyncClient, ASGITransport

    with patch("src.controllers.rides_controller.get_db") as mock_get_db:
        mock_db = AsyncMock()
        mock_get_db.return_value.__aenter__.return_value = mock_db

        with patch("src.controllers.rides_controller.service.list_active_user_ids") as mock_list_active:
            mock_list_active.return_value = ["USER_A", "USER_B"]

            async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
                response = await client.get("/rides/active-users")

            assert response.status_code == 200
            assert response.json() == ["USER_A", "USER_B"]


