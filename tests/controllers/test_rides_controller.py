from __future__ import annotations

import pytest
from unittest.mock import AsyncMock, Mock, patch
from fastapi.testclient import TestClient

from src.main import app
from src.controllers.rides_controller import EndRidePayload


@pytest.mark.asyncio
async def test_end_ride_controller_valid_payload():
    """Test POST /ride/end with valid payload."""
    client = TestClient(app)

    payload = {"ride_id": "RIDE001", "lon": 34.5, "lat": 32.5}

    with patch(
        "src.controllers.rides_controller.service.end_ride",
        new_callable=AsyncMock,
    ) as mock_end_ride:
        mock_end_ride.return_value = {
            "end_station_id": 1,
            "payment_charged": 15,
            "active_users": [],
        }

        response = client.post("/ride/end", json=payload)

        assert response.status_code == 200
        assert response.json()["end_station_id"] == 1
        assert response.json()["payment_charged"] == 15
        mock_end_ride.assert_called_once()


@pytest.mark.asyncio
async def test_end_ride_controller_missing_ride_id():
    """Test POST /ride/end with missing ride_id."""
    client = TestClient(app)

    payload = {"lon": 34.5, "lat": 32.5}  # Missing ride_id

    response = client.post("/ride/end", json=payload)

    assert response.status_code == 400  # Manual validation returns 400


@pytest.mark.asyncio
async def test_end_ride_controller_missing_lon():
    """Test POST /ride/end with missing lon."""
    client = TestClient(app)

    payload = {"ride_id": "RIDE001", "lat": 32.5}  # Missing lon

    response = client.post("/ride/end", json=payload)

    assert response.status_code == 400


@pytest.mark.asyncio
async def test_end_ride_controller_missing_lat():
    """Test POST /ride/end with missing lat."""
    client = TestClient(app)

    payload = {"ride_id": "RIDE001", "lon": 34.5}  # Missing lat

    response = client.post("/ride/end", json=payload)

    assert response.status_code == 400


@pytest.mark.asyncio
async def test_end_ride_controller_invalid_json():
    """Test POST /ride/end with invalid JSON."""
    client = TestClient(app)

    response = client.post("/ride/end", content="{invalid json")

    assert response.status_code == 400


@pytest.mark.asyncio
async def test_end_ride_controller_wrong_type():
    """Test POST /ride/end with wrong data types."""
    client = TestClient(app)

    payload = {"ride_id": "RIDE001", "lon": "not_a_number", "lat": 32.5}

    response = client.post("/ride/end", json=payload)

    assert response.status_code == 400  # Manual validation returns 400


@pytest.mark.asyncio
async def test_end_ride_payload_validation():
    """Test EndRidePayload validation."""
    # Valid payload
    valid = EndRidePayload(ride_id="RIDE001", lon=34.5, lat=32.5)
    assert valid.ride_id == "RIDE001"
    assert valid.lon == 34.5
    assert valid.lat == 32.5

    # Invalid payload (missing field)
    with pytest.raises(ValueError):
        EndRidePayload(ride_id="RIDE001", lon=34.5)  # Missing lat
