from __future__ import annotations

import pytest

from src.repositories.stations_repository import StationsRepository


@pytest.mark.asyncio
async def test_get_by_id(test_db):
    repo = StationsRepository()
    
    station = await repo.get_by_id(test_db, 1)
    
    assert station is not None
    assert station["station_id"] == 1
    assert station["name"] == "Test Station 1"
    assert station["lat"] == 32.0
    assert station["lon"] == 34.0
    assert station["max_capacity"] == 10


@pytest.mark.asyncio
async def test_get_by_id_not_found(test_db):
    repo = StationsRepository()
    
    station = await repo.get_by_id(test_db, 999)
    
    assert station is None


@pytest.mark.asyncio
async def test_get_nearest(test_db):
    repo = StationsRepository()
    
    # Query near station 1 (32.0, 34.0)
    station = await repo.get_nearest(test_db, lon=34.0, lat=32.0)
    
    assert station is not None
    assert station["station_id"] == 1
    assert "distance" in station


@pytest.mark.asyncio
async def test_get_nearest_returns_closest(test_db):
    repo = StationsRepository()
    
    # Query closer to station 2 (32.1, 34.1)
    station = await repo.get_nearest(test_db, lon=34.1, lat=32.1)
    
    assert station is not None
    assert station["station_id"] == 2
