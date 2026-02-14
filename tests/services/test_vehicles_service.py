from __future__ import annotations

import pytest
from unittest.mock import AsyncMock, Mock

from src.services.vehicles_service import VehiclesService
from src.repositories.vehicles_repository import VehiclesRepository


@pytest.mark.asyncio
async def test_get_vehicle_by_id():
    mock_repo = Mock(spec=VehiclesRepository)
    mock_repo.get_by_id = AsyncMock(return_value={
        "vehicle_id": "V001",
        "station_id": 1,
        "vehicle_type": "bicycle",
        "status": "available",
        "rides_since_last_treated": 5,
        "last_treated_date": "2025-01-01"
    })
    
    service = VehiclesService(repository=mock_repo)
    mock_db = Mock()
    
    result = await service.get_vehicle_by_id(mock_db, "V001")
    
    assert result is not None
    assert result["vehicle_id"] == "V001"
    assert result["vehicle_type"] == "bicycle"
    mock_repo.get_by_id.assert_called_once_with(mock_db, "V001")


@pytest.mark.asyncio
async def test_get_vehicle_by_id_not_found():
    mock_repo = Mock(spec=VehiclesRepository)
    mock_repo.get_by_id = AsyncMock(return_value=None)
    
    service = VehiclesService(repository=mock_repo)
    mock_db = Mock()
    
    result = await service.get_vehicle_by_id(mock_db, "V999")
    
    assert result is None
    mock_repo.get_by_id.assert_called_once_with(mock_db, "V999")


@pytest.mark.asyncio
async def test_list_vehicles():
    mock_repo = Mock(spec=VehiclesRepository)
    mock_repo.list_all = AsyncMock(return_value=[
        {"vehicle_id": "V001", "station_id": 1, "vehicle_type": "bicycle", "status": "available", "rides_since_last_treated": 5, "last_treated_date": "2025-01-01"},
        {"vehicle_id": "V002", "station_id": 1, "vehicle_type": "scooter", "status": "degraded", "rides_since_last_treated": 10, "last_treated_date": "2025-01-02"}
    ])
    
    service = VehiclesService(repository=mock_repo)
    mock_db = Mock()
    
    result = await service.list_vehicles(mock_db)
    
    assert len(result) == 2
    assert result[0]["vehicle_id"] == "V001"
    mock_repo.list_all.assert_called_once_with(mock_db)


@pytest.mark.asyncio
async def test_list_vehicles_by_station():
    mock_repo = Mock(spec=VehiclesRepository)
    mock_repo.list_by_station = AsyncMock(return_value=[
        {"vehicle_id": "V001", "station_id": 1, "vehicle_type": "bicycle", "status": "available", "rides_since_last_treated": 5, "last_treated_date": "2025-01-01"}
    ])
    
    service = VehiclesService(repository=mock_repo)
    mock_db = Mock()
    
    result = await service.list_vehicles_by_station(mock_db, 1)
    
    assert len(result) == 1
    assert result[0]["station_id"] == 1
    mock_repo.list_by_station.assert_called_once_with(mock_db, 1)
