from __future__ import annotations

import pytest
from unittest.mock import AsyncMock, Mock

from src.services.stations_service import StationsService
from src.repositories.stations_repository import StationsRepository


@pytest.mark.asyncio
async def test_get_station_by_id():
    mock_repo = Mock(spec=StationsRepository)
    mock_repo.get_by_id = AsyncMock(return_value={
        "station_id": 1,
        "name": "Test Station",
        "lat": 32.0,
        "lon": 34.0,
        "max_capacity": 10
    })
    
    service = StationsService(repository=mock_repo)
    mock_db = Mock()
    
    result = await service.get_station_by_id(mock_db, 1)
    
    assert result is not None
    assert result["station_id"] == 1
    assert result["name"] == "Test Station"
    mock_repo.get_by_id.assert_called_once_with(mock_db, 1)


@pytest.mark.asyncio
async def test_get_station_by_id_not_found():
    mock_repo = Mock(spec=StationsRepository)
    mock_repo.get_by_id = AsyncMock(return_value=None)
    
    service = StationsService(repository=mock_repo)
    mock_db = Mock()
    
    result = await service.get_station_by_id(mock_db, 999)
    
    assert result is None
    mock_repo.get_by_id.assert_called_once_with(mock_db, 999)


@pytest.mark.asyncio
async def test_get_nearest_station():
    mock_repo = Mock(spec=StationsRepository)
    mock_repo.get_nearest = AsyncMock(return_value={
        "station_id": 1,
        "name": "Nearest Station",
        "lat": 32.0,
        "lon": 34.0,
        "max_capacity": 10,
        "distance": 0.01
    })
    
    service = StationsService(repository=mock_repo)
    mock_db = Mock()
    
    result = await service.get_nearest_station(mock_db, lon=34.0, lat=32.0)
    
    assert result is not None
    assert result["station_id"] == 1
    assert "distance" in result
    mock_repo.get_nearest.assert_called_once_with(mock_db, lon=34.0, lat=32.0)
