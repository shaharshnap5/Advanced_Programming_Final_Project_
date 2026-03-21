from __future__ import annotations

from unittest.mock import AsyncMock, patch

import pytest
from httpx import ASGITransport, AsyncClient

from src.exceptions import ConflictException, NotFoundException, ValidationException
from src.main import app


@pytest.mark.asyncio
async def test_create_user_with_invalid_json_returns_400():
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        response = await client.post(
            "/users",
            content="{invalid json",
            headers={"content-type": "application/json"},
        )

    assert response.status_code == 400
    assert response.json()["detail"] == "Invalid JSON payload"


@pytest.mark.asyncio
async def test_create_user_conflict_returns_409():
    with patch("src.controllers.users_controller.get_db") as mock_get_db:
        mock_db = AsyncMock()
        mock_get_db.return_value.__aenter__.return_value = mock_db

        with patch("src.controllers.users_controller.service.create_user") as mock_create_user:
            mock_create_user.side_effect = ValueError("User already exists")

            async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
                response = await client.post("/users", json={"user_id": "USER001"})

    assert response.status_code == 409
    assert response.json()["detail"] == "User already exists"


@pytest.mark.asyncio
async def test_nearest_station_not_found_returns_404():
    with patch("src.controllers.stations_controller.get_db") as mock_get_db:
        mock_db = AsyncMock()
        mock_get_db.return_value.__aenter__.return_value = mock_db

        with patch("src.controllers.stations_controller.service.get_nearest_station") as mock_get:
            mock_get.return_value = None

            async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
                response = await client.get("/stations/nearest?lon=34.0&lat=32.0")

    assert response.status_code == 404
    assert response.json()["detail"] == "No stations found"


@pytest.mark.asyncio
async def test_register_invalid_payload_returns_400():
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        response = await client.post("/register", json={"name": "User"})

    assert response.status_code == 400


@pytest.mark.asyncio
async def test_global_handler_returns_409_for_register_conflict(isolated_client):
    with patch("src.controllers.register_controller.service.register_user") as mock_register_user:
        mock_register_user.side_effect = ConflictException("User already exists")

        response = await isolated_client.post(
            "/register",
            json={"name": "User", "credit_token": "tok_123"},
        )

    assert response.status_code == 409
    assert response.json()["detail"] == "User already exists"


@pytest.mark.asyncio
async def test_global_handler_returns_400_for_start_ride_bad_request(isolated_client):
    with patch("src.controllers.rides_controller.service.start_ride") as mock_start_ride:
        mock_start_ride.side_effect = ValidationException("No available vehicles at station 1")

        response = await isolated_client.post(
            "/ride/start",
            json={"user_id": "USER001", "lat": 32.0, "lon": 34.0},
        )

    assert response.status_code == 400
    assert response.json()["detail"] == "No available vehicles at station 1"


@pytest.mark.asyncio
async def test_global_handler_returns_404_for_missing_ride(isolated_client):
    with patch("src.controllers.rides_controller.service.end_ride") as mock_end_ride:
        mock_end_ride.side_effect = NotFoundException("Ride RIDE001 not found")

        response = await isolated_client.post(
            "/ride/end",
            json={"ride_id": "RIDE001", "lat": 32.1, "lon": 34.1},
        )

    assert response.status_code == 404
    assert response.json()["detail"] == "Ride RIDE001 not found"
