from __future__ import annotations

import pytest
from httpx import AsyncClient, ASGITransport
from unittest.mock import AsyncMock, patch

from src.main import app


# ============================================================================
# Tests for GET /stations/{station_id}
# ============================================================================

@pytest.mark.asyncio
async def test_get_station_success():
    """Test successfully retrieving a single station by ID."""
    with patch("src.controllers.stations_controller.get_db") as mock_get_db:
        mock_db = AsyncMock()
        mock_get_db.return_value.__aenter__.return_value = mock_db
        
        with patch("src.controllers.stations_controller.service.get_station_by_id") as mock_get:
            mock_get.return_value = {
                "station_id": 1,
                "name": "Test Station",
                "lat": 32.0,
                "lon": 34.0,
                "max_capacity": 10
            }
            
            async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
                response = await client.get("/stations/1")
            
            assert response.status_code == 200
            data = response.json()
            assert data["station_id"] == 1
            assert data["name"] == "Test Station"
            assert data["lat"] == 32.0
            assert data["lon"] == 34.0
            assert data["max_capacity"] == 10
            # Single station endpoint should NOT include distance
            assert "distance" not in data


@pytest.mark.asyncio
async def test_get_station_not_found():
    """Test retrieving a non-existent station returns 404."""
    with patch("src.controllers.stations_controller.get_db") as mock_get_db:
        mock_db = AsyncMock()
        mock_get_db.return_value.__aenter__.return_value = mock_db
        
        with patch("src.controllers.stations_controller.service.get_station_by_id") as mock_get:
            mock_get.return_value = None
            
            async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
                response = await client.get("/stations/999")
            
            assert response.status_code == 404
            assert response.json()["detail"] == "Station not found"


@pytest.mark.asyncio
async def test_get_station_returns_correct_model():
    """Test that station endpoint returns correct response model."""
    with patch("src.controllers.stations_controller.get_db") as mock_get_db:
        mock_db = AsyncMock()
        mock_get_db.return_value.__aenter__.return_value = mock_db

        with patch("src.controllers.stations_controller.service.get_station_by_id") as mock_get:
            mock_get.return_value = {
                "station_id": 5,
                "name": "Central Hub",
                "lat": 40.7128,
                "lon": -74.0060,
                "max_capacity": 50
            }

            async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
                response = await client.get("/stations/5")

            assert response.status_code == 200
            data = response.json()
            assert isinstance(data, dict)
            assert len(data) == 5  # Only 5 fields, no distance


# ============================================================================
# Tests for GET /stations/nearest
# ============================================================================

@pytest.mark.asyncio
async def test_get_nearest_station_success():
    """Test successfully retrieving the nearest station."""
    with patch("src.controllers.stations_controller.get_db") as mock_get_db:
        mock_db = AsyncMock()
        mock_get_db.return_value.__aenter__.return_value = mock_db
        
        with patch("src.controllers.stations_controller.service.get_nearest_station") as mock_get:
            mock_get.return_value = {
                "station_id": 1,
                "name": "Nearest Station",
                "lat": 32.0,
                "lon": 34.0,
                "max_capacity": 10,
                "distance": 0.14142135623730953  # sqrt(0.1^2 + 0.1^2)
            }
            
            async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
                response = await client.get("/stations/nearest?lon=34.0&lat=32.0")
            
            assert response.status_code == 200
            data = response.json()
            assert data["station_id"] == 1
            assert data["name"] == "Nearest Station"
            assert "distance" in data
            assert isinstance(data["distance"], float)
            assert data["distance"] >= 0


@pytest.mark.asyncio
async def test_get_nearest_station_with_distance_zero():
    """Test nearest station endpoint when user is at exact station location."""
    with patch("src.controllers.stations_controller.get_db") as mock_get_db:
        mock_db = AsyncMock()
        mock_get_db.return_value.__aenter__.return_value = mock_db

        with patch("src.controllers.stations_controller.service.get_nearest_station") as mock_get:
            mock_get.return_value = {
                "station_id": 1,
                "name": "Central Station",
                "lat": 32.0,
                "lon": 34.0,
                "max_capacity": 10,
                "distance": 0.0
            }

            async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
                response = await client.get("/stations/nearest?lon=34.0&lat=32.0")

            assert response.status_code == 200
            data = response.json()
            assert data["distance"] == 0.0


@pytest.mark.asyncio
async def test_get_nearest_station_missing_lon_param():
    """Test nearest endpoint without longitude parameter."""
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        response = await client.get("/stations/nearest?lat=32.0")

    assert response.status_code == 422  # Validation error


@pytest.mark.asyncio
async def test_get_nearest_station_missing_lat_param():
    """Test nearest endpoint without latitude parameter."""
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        response = await client.get("/stations/nearest?lon=34.0")

    assert response.status_code == 422  # Validation error


@pytest.mark.asyncio
async def test_get_nearest_station_missing_both_params():
    """Test nearest endpoint without any parameters."""
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        response = await client.get("/stations/nearest")
    
    assert response.status_code == 422  # Validation error


@pytest.mark.asyncio
async def test_get_nearest_station_not_found():
    """Test nearest endpoint when no station exists."""
    with patch("src.controllers.stations_controller.get_db") as mock_get_db:
        mock_db = AsyncMock()
        mock_get_db.return_value.__aenter__.return_value = mock_db

        with patch("src.controllers.stations_controller.service.get_nearest_station") as mock_get:
            mock_get.return_value = None

            async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
                response = await client.get("/stations/nearest?lon=34.0&lat=32.0")

            assert response.status_code == 404
            assert "No stations found" in response.json()["detail"]


@pytest.mark.asyncio
async def test_get_nearest_station_with_different_coordinates():
    """Test nearest endpoint with various coordinate combinations."""
    with patch("src.controllers.stations_controller.get_db") as mock_get_db:
        mock_db = AsyncMock()
        mock_get_db.return_value.__aenter__.return_value = mock_db

        with patch("src.controllers.stations_controller.service.get_nearest_station") as mock_get:
            test_cases = [
                (34.0, 32.0, 1, 0.0),
                (34.1, 32.1, 2, 0.14142),
                (-74.0060, 40.7128, 5, 0.5),
            ]

            async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
                for lon, lat, station_id, distance in test_cases:
                    mock_get.return_value = {
                        "station_id": station_id,
                        "name": f"Station {station_id}",
                        "lat": lat,
                        "lon": lon,
                        "max_capacity": 10,
                        "distance": distance
                    }

                    response = await client.get(f"/stations/nearest?lon={lon}&lat={lat}")

                    assert response.status_code == 200
                    data = response.json()
                    assert data["station_id"] == station_id
                    assert "distance" in data


@pytest.mark.asyncio
async def test_get_nearest_station_returns_station_with_distance_model():
    """Test that nearest endpoint returns StationWithDistance model."""
    with patch("src.controllers.stations_controller.get_db") as mock_get_db:
        mock_db = AsyncMock()
        mock_get_db.return_value.__aenter__.return_value = mock_db

        with patch("src.controllers.stations_controller.service.get_nearest_station") as mock_get:
            mock_get.return_value = {
                "station_id": 1,
                "name": "Test Station",
                "lat": 32.0,
                "lon": 34.0,
                "max_capacity": 10,
                "distance": 0.1
            }

            async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
                response = await client.get("/stations/nearest?lon=34.0&lat=32.0")

            assert response.status_code == 200
            data = response.json()
            # Verify all required fields are present
            required_fields = ["station_id", "name", "lat", "lon", "max_capacity", "distance"]
            for field in required_fields:
                assert field in data, f"Missing field: {field}"


@pytest.mark.asyncio
async def test_get_nearest_station_with_float_coordinates():
    """Test nearest endpoint with floating-point coordinates."""
    with patch("src.controllers.stations_controller.get_db") as mock_get_db:
        mock_db = AsyncMock()
        mock_get_db.return_value.__aenter__.return_value = mock_db

        with patch("src.controllers.stations_controller.service.get_nearest_station") as mock_get:
            mock_get.return_value = {
                "station_id": 1,
                "name": "Station",
                "lat": 32.123456,
                "lon": 34.654321,
                "max_capacity": 10,
                "distance": 0.123456
            }

            async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
                response = await client.get("/stations/nearest?lon=34.654321&lat=32.123456")

            assert response.status_code == 200
            data = response.json()
            assert abs(data["distance"] - 0.123456) < 0.000001


@pytest.mark.asyncio
async def test_get_nearest_station_with_negative_coordinates():
    """Test nearest endpoint with negative coordinates (e.g., Western hemisphere)."""
    with patch("src.controllers.stations_controller.get_db") as mock_get_db:
        mock_db = AsyncMock()
        mock_get_db.return_value.__aenter__.return_value = mock_db

        with patch("src.controllers.stations_controller.service.get_nearest_station") as mock_get:
            mock_get.return_value = {
                "station_id": 1,
                "name": "NYC Station",
                "lat": 40.7128,
                "lon": -74.0060,
                "max_capacity": 50,
                "distance": 0.0
            }

            async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
                response = await client.get("/stations/nearest?lon=-74.0060&lat=40.7128")

            assert response.status_code == 200
            data = response.json()
            assert data["lon"] == -74.0060
            assert data["lat"] == 40.7128


