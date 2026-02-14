from __future__ import annotations

import pytest
from httpx import AsyncClient, ASGITransport
from unittest.mock import AsyncMock, patch

from src.main import app


@pytest.mark.asyncio
async def test_get_station_success():
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


@pytest.mark.asyncio
async def test_get_station_not_found():
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
async def test_get_nearest_station():
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
                "distance": 0.01
            }
            
            async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
                response = await client.get("/stations/nearest?lon=34.0&lat=32.0")
            
            assert response.status_code == 200
            data = response.json()
            assert data["station_id"] == 1
            assert "distance" in data


@pytest.mark.asyncio
async def test_get_nearest_station_missing_params():
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        response = await client.get("/stations/nearest")
    
    assert response.status_code == 422  # Validation error
