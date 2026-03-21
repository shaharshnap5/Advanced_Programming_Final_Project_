"""Tests for RideController."""

from __future__ import annotations

import pytest
from unittest.mock import AsyncMock, Mock, patch
from datetime import datetime
from fastapi import HTTPException

from src.schemas.ride_schemas import RideStartRequest
from src.models.ride import Ride
from src.models.user import User
from src.main import app


@pytest.mark.asyncio
async def test_start_ride_success():
    """Test successfully starting a ride."""
    # Import the endpoint function directly
    from src.controllers.rides_controller import start_ride

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
        is_degraded_report=False,
    )

    # We need to patch the RideService within the controller
    with patch("src.controllers.rides_controller.service") as mock_service:
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
    from src.controllers.rides_controller import start_ride

    request = RideStartRequest(user_id="USER001", lon=34.0, lat=32.0)
    mock_db = Mock()

    with patch("src.controllers.rides_controller.service") as mock_service:
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
    from src.controllers.rides_controller import start_ride

    request = RideStartRequest(user_id="USER001", lon=34.0, lat=32.0)
    mock_db = Mock()

    with patch("src.controllers.rides_controller.service") as mock_service:
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
    from src.controllers.rides_controller import start_ride

    request = RideStartRequest(user_id="USER001", lon=34.0, lat=32.0)
    mock_db = Mock()

    with patch("src.controllers.rides_controller.service") as mock_service:
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
    from src.controllers.rides_controller import start_ride

    request = RideStartRequest(user_id="USER_MODEL", lon=34.5, lat=32.5)
    mock_db = Mock()

    expected_ride = Ride(
        ride_id="RIDE_MODEL_TEST",
        user_id="USER_MODEL",
        vehicle_id="V_MODEL",
        start_station_id=3,
        start_time=datetime(2026, 3, 17, 12, 0),
        is_degraded_report=False,
    )

    with patch("src.controllers.rides_controller.service") as mock_service:
        mock_service.start_new_ride = AsyncMock(return_value=expected_ride)

        result = await start_ride(request, mock_db)

        # Verify it's a valid Ride instance
        assert isinstance(result, Ride)
        assert result.ride_id == "RIDE_MODEL_TEST"
        assert result.start_station_id == 3


@pytest.mark.asyncio
async def test_start_ride_none_return():
    """Test handling when service returns None."""
    from src.controllers.rides_controller import start_ride

    request = RideStartRequest(user_id="USER001", lon=34.0, lat=32.0)
    mock_db = Mock()

    with patch("src.controllers.rides_controller.service") as mock_service:
        mock_service.start_new_ride = AsyncMock(return_value=None)

        # Should raise HTTPException
        with pytest.raises(HTTPException) as exc_info:
            await start_ride(request, mock_db)

        # 404 is correct when ride could not be started (not found)
        assert exc_info.value.status_code == 404
        assert "Could not start ride" in exc_info.value.detail


@pytest.mark.asyncio
async def test_start_ride_with_coordinates_payload():
    """/rides/start should support location payload."""
    from fastapi.testclient import TestClient

    client = TestClient(app)
    expected_ride = {
        "ride_id": "RIDE_001",
        "user_id": "USER001",
        "vehicle_id": "V001",
        "start_station_id": 1,
        "end_station_id": None,
        "start_time": "2026-03-20T12:00:00",
        "end_time": None,
        "is_degraded_report": False,
    }

    with patch(
        "src.controllers.rides_controller.service.start_new_ride",
        new_callable=AsyncMock,
    ) as mock_start:
        mock_start.return_value = Ride(**expected_ride)

        response = client.post(
            "/rides/start", json={"user_id": "USER001", "lon": 34.0, "lat": 32.0}
        )

        assert response.status_code == 200
        assert response.json()["ride_id"] == "RIDE_001"
        mock_start.assert_called_once()


@pytest.mark.asyncio
async def test_get_active_users_via_api():
    from httpx import AsyncClient, ASGITransport

    with patch(
        "src.controllers.rides_controller.service.list_active_users"
    ) as mock_list_active:
        mock_list_active.return_value = [
            User(
                user_id="USER_A",
                first_name="A",
                last_name="A",
                email="a@example.com",
                payment_token="tok1",
            ),
            User(
                user_id="USER_B",
                first_name="B",
                last_name="B",
                email="b@example.com",
                payment_token="tok2",
            ),
        ]

        async with AsyncClient(
            transport=ASGITransport(app=app), base_url="http://test"
        ) as client:
            response = await client.get("/rides/active-users")

        assert response.status_code == 200
        assert response.json() == [
            {
                "user_id": "USER_A",
                "first_name": "A",
                "last_name": "A",
                "email": "a@example.com",
                "payment_token": "tok1",
            },
            {
                "user_id": "USER_B",
                "first_name": "B",
                "last_name": "B",
                "email": "b@example.com",
                "payment_token": "tok2",
            },
        ]


# ============ END RIDE TESTS ============


@pytest.mark.asyncio
async def test_end_ride_endpoint_valid_payload():
    """Test POST /ride/end with valid JSON payload."""
    from fastapi.testclient import TestClient
    from src.main import app

    client = TestClient(app)
    payload = {
        "ride_id": "RIDE_12345",
        "lon": 34.5,
        "lat": 32.5,
    }

    with patch(
        "src.controllers.rides_controller.service.end_ride", new_callable=AsyncMock
    ) as mock_end_ride:
        mock_end_ride.return_value = {
            "end_station_id": 5,
            "payment_charged": 15,
            "vehicle": {
                "vehicle_id": "V001",
                "station_id": 5,
                "vehicle_type": "electric_bicycle",
                "status": "available",
                "rides_since_last_treated": 4,
                "last_treated_date": None,
                "battery": 86,
            },
        }

        response = client.post("/rides/end", json=payload)

        assert response.status_code == 200
        data = response.json()
        assert data["end_station_id"] == 5
        assert data["payment_charged"] == 15
        assert data["vehicle"]["battery"] == 86
        mock_end_ride.assert_called_once()


@pytest.mark.asyncio
async def test_end_ride_endpoint_missing_ride_id():
    """Test POST /ride/end with missing ride_id."""
    from fastapi.testclient import TestClient
    from src.main import app

    client = TestClient(app)
    payload = {
        "lon": 34.5,
        "lat": 32.5,
        # Missing: "ride_id"
    }

    response = client.post("/rides/end", json=payload)

    # Pydantic validation should fail
    assert response.status_code == 422


@pytest.mark.asyncio
async def test_end_ride_endpoint_missing_lon():
    """Test POST /ride/end with missing lon."""
    from fastapi.testclient import TestClient
    from src.main import app

    client = TestClient(app)
    payload = {
        "ride_id": "RIDE_001",
        "lat": 32.5,
        # Missing: "lon"
    }

    response = client.post("/rides/end", json=payload)

    assert response.status_code == 422


@pytest.mark.asyncio
async def test_end_ride_endpoint_missing_lat():
    """Test POST /ride/end with missing lat."""
    from fastapi.testclient import TestClient
    from src.main import app

    client = TestClient(app)
    payload = {
        "ride_id": "RIDE_001",
        "lon": 34.5,
        # Missing: "lat"
    }

    response = client.post("/rides/end", json=payload)

    assert response.status_code == 422


@pytest.mark.asyncio
async def test_end_ride_endpoint_invalid_json():
    """Test POST /ride/end with invalid JSON."""
    from fastapi.testclient import TestClient
    from src.main import app

    client = TestClient(app)
    response = client.post("/rides/end", content="{invalid json")

    # FastAPI returns 422 for validation errors
    assert response.status_code == 422


@pytest.mark.asyncio
async def test_end_ride_endpoint_wrong_types():
    """Test POST /ride/end with wrong data types."""
    from fastapi.testclient import TestClient
    from src.main import app

    client = TestClient(app)
    payload = {
        "ride_id": "RIDE_001",
        "lon": "not_a_number",  # Should be float
        "lat": 32.5,
    }

    response = client.post("/rides/end", json=payload)

    assert response.status_code == 422


@pytest.mark.asyncio
async def test_end_ride_endpoint_service_error():
    """Test POST /ride/end when service raises an error."""
    from fastapi.testclient import TestClient
    from src.main import app

    client = TestClient(app)
    payload = {
        "ride_id": "RIDE_MISSING",
        "lon": 34.5,
        "lat": 32.5,
    }

    with patch(
        "src.controllers.rides_controller.service.end_ride", new_callable=AsyncMock
    ) as mock_end_ride:
        mock_end_ride.side_effect = HTTPException(
            status_code=404, detail="Ride not found"
        )

        response = client.post("/rides/end", json=payload)

        assert response.status_code == 404
        assert "Ride not found" in response.json()["detail"]


@pytest.mark.asyncio
async def test_end_ride_endpoint_response_structure():
    """Test that response includes all required fields."""
    from fastapi.testclient import TestClient
    from src.main import app

    client = TestClient(app)
    payload = {
        "ride_id": "RIDE_001",
        "lon": 34.5,
        "lat": 32.5,
    }

    with patch(
        "src.controllers.rides_controller.service.end_ride", new_callable=AsyncMock
    ) as mock_end_ride:
        mock_end_ride.return_value = {
            "end_station_id": 1,
            "payment_charged": 15,
            "vehicle": {
                "vehicle_id": "V002",
                "station_id": 1,
                "vehicle_type": "bicycle",
                "status": "available",
                "rides_since_last_treated": 6,
                "last_treated_date": None,
                "battery": None,
            },
        }

        response = client.post("/rides/end", json=payload)

        assert response.status_code == 200
        data = response.json()

        # Verify all required fields exist
        assert "end_station_id" in data
        assert "payment_charged" in data
        assert "vehicle" in data

        # Verify types
        assert isinstance(data["end_station_id"], int)
        assert isinstance(data["payment_charged"], int)
        assert isinstance(data["vehicle"], dict)
