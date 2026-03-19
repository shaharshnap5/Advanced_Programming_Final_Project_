"""
Integration tests for global exception handling.
Verifies that generic handlers properly catch exceptions and return appropriate status codes.
"""

import pytest
from httpx import AsyncClient, ASGITransport
from unittest.mock import AsyncMock, patch

from src.main import app
from src.exceptions import ValidationException, NotFoundException, ConflictException


@pytest.mark.asyncio
async def test_unhandled_exception_returns_502():
    """Test that unhandled exceptions return 502 Bad Gateway."""
    with patch("src.controllers.vehicles_controller.get_db") as mock_get_db:
        mock_db = AsyncMock()
        mock_get_db.return_value.__aenter__.return_value = mock_db

        with patch("src.controllers.vehicles_controller.service.treat_vehicle") as mock_treat:
            mock_treat.side_effect = ValidationException("Vehicle not eligible for treatment")

            async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
                response = await client.post("/vehicles/V001/treat")

            assert response.status_code == 502
            assert response.json()["detail"] == "Internal server error"


@pytest.mark.asyncio
async def test_not_found_exception_returns_502():
    """Test that NotFoundException returns 502 (caught by generic handler)."""
    with patch("src.controllers.vehicles_controller.get_db") as mock_get_db:
        mock_db = AsyncMock()
        mock_get_db.return_value.__aenter__.return_value = mock_db

        with patch("src.controllers.vehicles_controller.service.get_vehicle_by_id") as mock_get:
            mock_get.side_effect = NotFoundException("Vehicle not found")

            async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
                response = await client.get("/vehicles/NONEXISTENT")

            assert response.status_code == 502
            assert response.json()["detail"] == "Internal server error"


@pytest.mark.asyncio
async def test_conflict_exception_returns_502():
    """Test that ConflictException returns 502 (caught by generic handler)."""
    with patch("src.controllers.users_controller.get_db") as mock_get_db:
        mock_db = AsyncMock()
        mock_get_db.return_value.__aenter__.return_value = mock_db

        with patch("src.controllers.users_controller.service.create_user") as mock_create:
            mock_create.side_effect = ConflictException("User already exists")

            async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
                response = await client.post(
                    "/users/register",
                    json={
                        "user_id": "USER001",
                        "first_name": "Test",
                        "last_name": "User",
                        "email": "test@example.com"
                    }
                )

            assert response.status_code == 502
            assert response.json()["detail"] == "Internal server error"


@pytest.mark.asyncio
async def test_nonexistent_route_returns_404():
    """Test that requests to non-existent routes return 404."""
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        response = await client.get("/asdasd")

    assert response.status_code == 404
    assert response.json()["detail"] == "Route not found"


@pytest.mark.asyncio
async def test_another_nonexistent_route_returns_404():
    """Test that POST to non-existent route returns 404."""
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        response = await client.post("/fake/endpoint", json={})

    assert response.status_code == 404
    assert response.json()["detail"] == "Route not found"


@pytest.mark.asyncio
async def test_generic_exception_returns_502():
    """Test that a generic Exception returns 502."""
    with patch("src.controllers.stations_controller.get_db") as mock_get_db:
        mock_db = AsyncMock()
        mock_get_db.return_value.__aenter__.return_value = mock_db

        with patch("src.controllers.stations_controller.service.get_all_stations") as mock_get:
            mock_get.side_effect = Exception("Unexpected error")

            async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
                response = await client.get("/stations")

            assert response.status_code == 502
            assert response.json()["detail"] == "Internal server error"
