from __future__ import annotations

from datetime import date
from unittest.mock import AsyncMock, patch

import pytest
from httpx import ASGITransport, AsyncClient

from src.main import app
from src.models.vehicle import VehicleStatus, VehicleType


@pytest.mark.asyncio
async def test_treat_vehicle_success():
    with patch("src.controllers.vehicle_controller.get_db") as mock_get_db:
        mock_db = AsyncMock()
        mock_get_db.return_value.__aenter__.return_value = mock_db

        with patch("src.controllers.vehicle_controller.service.treat_vehicle") as mock_treat:
            mock_treat.return_value = {
                "vehicle_id": "V001",
                "station_id": 2,
                "vehicle_type": VehicleType.bike,
                "status": VehicleStatus.available,
                "rides_since_last_treated": 0,
                "last_treated_date": date.today(),
            }

            async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
                response = await client.post("/vehicle/treat", json={"vehicle_id": "V001", "station_id": 2})

            assert response.status_code == 200
            data = response.json()
            assert data["vehicle_id"] == "V001"
            assert data["status"] == "available"


@pytest.mark.asyncio
async def test_report_vehicle_degraded_success():
    with patch("src.controllers.vehicle_controller.get_db") as mock_get_db:
        mock_db = AsyncMock()
        mock_get_db.return_value.__aenter__.return_value = mock_db

        with patch("src.controllers.vehicle_controller.service.report_vehicle_degraded") as mock_report:
            mock_report.return_value = {
                "vehicle_id": "V010",
                "station_id": 1,
                "vehicle_type": VehicleType.bike,
                "status": VehicleStatus.degraded,
                "rides_since_last_treated": 3,
                "last_treated_date": date(2025, 1, 1),
            }

            async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
                response = await client.post("/vehicle/report-degraded", json={"vehicle_id": "V010"})

            assert response.status_code == 200
            data = response.json()
            assert data["vehicle_id"] == "V010"
            assert data["status"] == "degraded"


@pytest.mark.asyncio
async def test_get_nearest_station_success():
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
                "vehicles": ["V001"],
                "distance": 0.01,
            }

            async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
                response = await client.get("/stations/nearest?lon=34.0&lat=32.0")

            assert response.status_code == 200
            data = response.json()
            assert data["station_id"] == 1
            assert data["distance"] == 0.01


@pytest.mark.asyncio
async def test_get_active_users_success():
    with patch("src.controllers.rides_controller.get_db") as mock_get_db:
        mock_db = AsyncMock()
        mock_get_db.return_value.__aenter__.return_value = mock_db

        with patch("src.controllers.rides_controller.service.get_active_users") as mock_get_active_users:
            mock_get_active_users.return_value = ["USER_A", "USER_B"]

            async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
                response = await client.get("/rides/active-users")

            assert response.status_code == 200
            assert response.json()["active_users"] == ["USER_A", "USER_B"]
