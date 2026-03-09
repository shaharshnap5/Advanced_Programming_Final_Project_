from __future__ import annotations

import pytest
from httpx import AsyncClient, ASGITransport
from unittest.mock import AsyncMock, patch

from src.main import app


@pytest.mark.asyncio
async def test_get_vehicle_success():
    with patch("src.controllers.vehicles_controller.get_db") as mock_get_db:
        mock_db = AsyncMock()
        mock_get_db.return_value.__aenter__.return_value = mock_db
        
        with patch("src.controllers.vehicles_controller.service.get_vehicle_by_id") as mock_get:
            mock_get.return_value = {
                "vehicle_id": "V001",
                "station_id": 1,
                "vehicle_type": "bicycle",
                "status": "available",
                "rides_since_last_treated": 5,
                "last_treated_date": "2025-01-01"
            }
            
            async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
                response = await client.get("/vehicles/V001")
            
            assert response.status_code == 200
            data = response.json()
            assert data["vehicle_id"] == "V001"
            assert data["vehicle_type"] == "bicycle"


@pytest.mark.asyncio
async def test_get_vehicle_not_found():
    with patch("src.controllers.vehicles_controller.get_db") as mock_get_db:
        mock_db = AsyncMock()
        mock_get_db.return_value.__aenter__.return_value = mock_db
        
        with patch("src.controllers.vehicles_controller.service.get_vehicle_by_id") as mock_get:
            mock_get.return_value = None
            
            async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
                response = await client.get("/vehicles/V999")
            
            assert response.status_code == 404
            assert response.json()["detail"] == "Vehicle not found"


@pytest.mark.asyncio
async def test_list_vehicles():
    with patch("src.controllers.vehicles_controller.get_db") as mock_get_db:
        mock_db = AsyncMock()
        mock_get_db.return_value.__aenter__.return_value = mock_db
        
        with patch("src.controllers.vehicles_controller.service.list_vehicles") as mock_list:
            mock_list.return_value = [
                {"vehicle_id": "V001", "station_id": 1, "vehicle_type": "bicycle", "status": "available", "rides_since_last_treated": 5, "last_treated_date": "2025-01-01"},
                {"vehicle_id": "V002", "station_id": 1, "vehicle_type": "scooter", "status": "degraded", "rides_since_last_treated": 10, "last_treated_date": "2025-01-02"}
            ]
            
            async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
                response = await client.get("/vehicles")
            
            assert response.status_code == 200
            data = response.json()
            assert len(data) == 2
            assert data[0]["vehicle_id"] == "V001"


@pytest.mark.asyncio
async def test_list_vehicles_by_station():
    with patch("src.controllers.vehicles_controller.get_db") as mock_get_db:
        mock_db = AsyncMock()
        mock_get_db.return_value.__aenter__.return_value = mock_db
        
        with patch("src.controllers.vehicles_controller.service.list_vehicles_by_station") as mock_list:
            mock_list.return_value = [
                {"vehicle_id": "V001", "station_id": 1, "vehicle_type": "bicycle", "status": "available", "rides_since_last_treated": 5, "last_treated_date": "2025-01-01"}
            ]
            
            async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
                response = await client.get("/vehicles?station_id=1")
            
            assert response.status_code == 200
            data = response.json()
            assert len(data) == 1
            assert data[0]["station_id"] == 1

@pytest.mark.asyncio
async def test_list_vehicles_eligible_for_treatment():
    """Test listing vehicles eligible for treatment."""
    with patch("src.controllers.vehicles_controller.get_db") as mock_get_db:
        mock_db = AsyncMock()
        mock_get_db.return_value.__aenter__.return_value = mock_db
        
        with patch("src.controllers.vehicles_controller.service.list_vehicles_eligible_for_treatment") as mock_list:
            mock_list.return_value = [
                {"vehicle_id": "V001", "station_id": 1, "vehicle_type": "bicycle", "status": "degraded", "rides_since_last_treated": 10, "last_treated_date": "2025-01-01"},
                {"vehicle_id": "V002", "station_id": 1, "vehicle_type": "scooter", "status": "available", "rides_since_last_treated": 7, "last_treated_date": "2025-01-02"}
            ]
            
            async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
                response = await client.get("/vehicles/treatment/eligible")
            
            assert response.status_code == 200
            data = response.json()
            assert len(data) == 2


@pytest.mark.asyncio
async def test_treat_vehicle_success():
    """Test successful vehicle treatment."""
    with patch("src.controllers.vehicles_controller.get_db") as mock_get_db:
        mock_db = AsyncMock()
        mock_get_db.return_value.__aenter__.return_value = mock_db
        
        with patch("src.controllers.vehicles_controller.service.treat_vehicle") as mock_treat:
            mock_treat.return_value = {
                "vehicle_id": "V001",
                "station_id": 1,
                "vehicle_type": "bicycle",
                "status": "available",
                "rides_since_last_treated": 0,
                "last_treated_date": "2025-03-09"
            }
            
            async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
                response = await client.post("/vehicles/V001/treat")
            
            assert response.status_code == 200
            data = response.json()
            assert data["status"] == "available"
            assert data["rides_since_last_treated"] == 0


@pytest.mark.asyncio
async def test_treat_vehicle_with_station():
    """Test vehicle treatment with station assignment."""
    with patch("src.controllers.vehicles_controller.get_db") as mock_get_db:
        mock_db = AsyncMock()
        mock_get_db.return_value.__aenter__.return_value = mock_db
        
        with patch("src.controllers.vehicles_controller.service.treat_vehicle") as mock_treat:
            mock_treat.return_value = {
                "vehicle_id": "V004",
                "station_id": 3,
                "vehicle_type": "bicycle",
                "status": "available",
                "rides_since_last_treated": 0,
                "last_treated_date": "2025-03-09"
            }
            
            async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
                response = await client.post("/vehicles/V004/treat?station_id=3")
            
            assert response.status_code == 200
            data = response.json()
            assert data["station_id"] == 3
            mock_treat.assert_called_once()


@pytest.mark.asyncio
async def test_treat_vehicle_not_eligible():
    """Test treatment fails for non-eligible vehicle."""
    with patch("src.controllers.vehicles_controller.get_db") as mock_get_db:
        mock_db = AsyncMock()
        mock_get_db.return_value.__aenter__.return_value = mock_db
        
        with patch("src.controllers.vehicles_controller.service.treat_vehicle") as mock_treat:
            mock_treat.side_effect = ValueError("Vehicle V003 is not eligible for treatment")
            
            async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
                response = await client.post("/vehicles/V003/treat")
            
            assert response.status_code == 400


@pytest.mark.asyncio
async def test_treat_vehicle_needs_station():
    """Test treatment fails for degraded vehicle without station."""
    with patch("src.controllers.vehicles_controller.get_db") as mock_get_db:
        mock_db = AsyncMock()
        mock_get_db.return_value.__aenter__.return_value = mock_db
        
        with patch("src.controllers.vehicles_controller.service.treat_vehicle") as mock_treat:
            mock_treat.side_effect = ValueError("Must provide a station_id")
            
            async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
                response = await client.post("/vehicles/V004/treat")
            
            assert response.status_code == 400