from __future__ import annotations

import pytest

from src.repositories.vehicles_repository import VehiclesRepository


@pytest.mark.asyncio
async def test_get_by_id(test_db):
    repo = VehiclesRepository()
    
    vehicle = await repo.get_by_id(test_db, "V001")
    
    assert vehicle is not None
    assert vehicle["vehicle_id"] == "V001"
    assert vehicle["station_id"] == 1
    assert vehicle["vehicle_type"] == "bicycle"
    assert vehicle["status"] == "available"
    assert vehicle["rides_since_last_treated"] == 5


@pytest.mark.asyncio
async def test_get_by_id_not_found(test_db):
    repo = VehiclesRepository()
    
    vehicle = await repo.get_by_id(test_db, "V999")
    
    assert vehicle is None


@pytest.mark.asyncio
async def test_list_all(test_db):
    repo = VehiclesRepository()
    
    vehicles = await repo.list_all(test_db)
    
    assert len(vehicles) == 2
    assert vehicles[0]["vehicle_id"] == "V001"
    assert vehicles[1]["vehicle_id"] == "V002"


@pytest.mark.asyncio
async def test_list_by_station(test_db):
    repo = VehiclesRepository()
    
    vehicles = await repo.list_by_station(test_db, 1)
    
    assert len(vehicles) == 2
    for vehicle in vehicles:
        assert vehicle["station_id"] == 1


@pytest.mark.asyncio
async def test_list_by_station_empty(test_db):
    repo = VehiclesRepository()
    
    vehicles = await repo.list_by_station(test_db, 999)
    
    assert len(vehicles) == 0
