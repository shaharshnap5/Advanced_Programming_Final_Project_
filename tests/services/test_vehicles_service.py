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

@pytest.mark.asyncio
async def test_list_vehicles_eligible_for_treatment():
    """Test listing vehicles eligible for treatment."""
    mock_repo = Mock(spec=VehiclesRepository)
    mock_repo.list_vehicles_eligible_for_treatment = AsyncMock(return_value=[
        {"vehicle_id": "V001", "station_id": 1, "vehicle_type": "bicycle", "status": "degraded", "rides_since_last_treated": 10, "last_treated_date": "2025-01-01"},
        {"vehicle_id": "V002", "station_id": 1, "vehicle_type": "scooter", "status": "available", "rides_since_last_treated": 7, "last_treated_date": "2025-01-02"}
    ])
    
    service = VehiclesService(repository=mock_repo)
    mock_db = Mock()
    
    result = await service.list_vehicles_eligible_for_treatment(mock_db)
    
    assert len(result) == 2
    mock_repo.list_vehicles_eligible_for_treatment.assert_called_once_with(mock_db)


@pytest.mark.asyncio
async def test_treat_vehicle_degraded_with_station():
    """Test treating a degraded vehicle that already has a station."""
    mock_repo = Mock(spec=VehiclesRepository)
    mock_repo.get_by_id = AsyncMock(side_effect=[
        {"vehicle_id": "V001", "station_id": 1, "vehicle_type": "bicycle", "status": "degraded", "rides_since_last_treated": 10, "last_treated_date": "2025-01-01"},
        {"vehicle_id": "V001", "station_id": 1, "vehicle_type": "bicycle", "status": "available", "rides_since_last_treated": 0, "last_treated_date": "2025-03-09"}
    ])
    mock_repo.treat_vehicle = AsyncMock(return_value=True)
    
    service = VehiclesService(repository=mock_repo)
    mock_db = Mock()
    
    result = await service.treat_vehicle(mock_db, "V001")
    
    assert result["status"] == "available"
    assert result["rides_since_last_treated"] == 0
    mock_repo.treat_vehicle.assert_called_once_with(mock_db, "V001", 1)


@pytest.mark.asyncio
async def test_treat_vehicle_rides_threshold():
    """Test treating a vehicle that reached rides threshold but not degraded."""
    mock_repo = Mock(spec=VehiclesRepository)
    mock_repo.get_by_id = AsyncMock(side_effect=[
        {"vehicle_id": "V002", "station_id": 2, "vehicle_type": "scooter", "status": "available", "rides_since_last_treated": 7, "last_treated_date": "2025-01-02"},
        {"vehicle_id": "V002", "station_id": 2, "vehicle_type": "scooter", "status": "available", "rides_since_last_treated": 0, "last_treated_date": "2025-03-09"}
    ])
    mock_repo.treat_vehicle = AsyncMock(return_value=True)
    
    service = VehiclesService(repository=mock_repo)
    mock_db = Mock()
    
    result = await service.treat_vehicle(mock_db, "V002")
    
    assert result["status"] == "available"
    assert result["rides_since_last_treated"] == 0


@pytest.mark.asyncio
async def test_treat_vehicle_not_eligible():
    """Test that treatment fails for non-eligible vehicle."""
    mock_repo = Mock(spec=VehiclesRepository)
    mock_repo.get_by_id = AsyncMock(return_value={
        "vehicle_id": "V003", "station_id": 1, "vehicle_type": "bicycle", "status": "available", "rides_since_last_treated": 3, "last_treated_date": "2025-01-03"
    })
    
    service = VehiclesService(repository=mock_repo)
    mock_db = Mock()
    
    with pytest.raises(ValueError, match="not eligible for treatment"):
        await service.treat_vehicle(mock_db, "V003")


@pytest.mark.asyncio
async def test_treat_vehicle_degraded_needs_station():
    """Test that treatment fails for degraded vehicle without station."""
    mock_repo = Mock(spec=VehiclesRepository)
    mock_repo.get_by_id = AsyncMock(return_value={
        "vehicle_id": "V004", "station_id": None, "vehicle_type": "bicycle", "status": "degraded", "rides_since_last_treated": 10, "last_treated_date": "2025-01-04"
    })
    
    service = VehiclesService(repository=mock_repo)
    mock_db = Mock()
    
    with pytest.raises(ValueError, match="Must provide a station_id"):
        await service.treat_vehicle(mock_db, "V004")


@pytest.mark.asyncio
async def test_treat_vehicle_degraded_assign_station():
    """Test treating a degraded vehicle by assigning a station."""
    mock_repo = Mock(spec=VehiclesRepository)
    mock_repo.get_by_id = AsyncMock(side_effect=[
        {"vehicle_id": "V004", "station_id": None, "vehicle_type": "bicycle", "status": "degraded", "rides_since_last_treated": 10, "last_treated_date": "2025-01-04"},
        {"vehicle_id": "V004", "station_id": 3, "vehicle_type": "bicycle", "status": "available", "rides_since_last_treated": 0, "last_treated_date": "2025-03-09"}
    ])
    mock_repo.treat_vehicle = AsyncMock(return_value=True)
    
    service = VehiclesService(repository=mock_repo)
    mock_db = Mock()
    
    result = await service.treat_vehicle(mock_db, "V004", station_id=3)
    
    assert result["status"] == "available"
    assert result["rides_since_last_treated"] == 0
    assert result["station_id"] == 3
    mock_repo.treat_vehicle.assert_called_once_with(mock_db, "V004", 3)