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

@pytest.mark.asyncio
async def test_list_vehicles_eligible_for_treatment(test_db):
    """Test listing vehicles eligible for treatment (degraded OR rides >= 7)."""
    repo = VehiclesRepository()
    
    # Set V002 to have 7 rides (meets treatment threshold)
    await test_db.execute(
        "UPDATE vehicles SET rides_since_last_treated = 7 WHERE vehicle_id = 'V002'"
    )
    await test_db.commit()
    
    eligible = await repo.list_vehicles_eligible_for_treatment(test_db)
    
    # Should include V002 (rides >= 7)
    vehicle_ids = [v["vehicle_id"] for v in eligible]
    assert "V002" in vehicle_ids
    
    # Verify rides count
    for vehicle in eligible:
        if vehicle["vehicle_id"] == "V002":
            assert vehicle["rides_since_last_treated"] >= 7


@pytest.mark.asyncio
async def test_treat_vehicle_success(test_db):
    """Test successful treatment of a vehicle."""
    repo = VehiclesRepository()
    
    # Set V001 to have high rides count (eligible for treatment)
    await test_db.execute(
        "UPDATE vehicles SET rides_since_last_treated = 10 WHERE vehicle_id = 'V001'"
    )
    await test_db.commit()
    
    # Treat the vehicle
    result = await repo.treat_vehicle(test_db, "V001", station_id=2)
    
    assert result is True
    
    # Verify treatment applied
    vehicle = await repo.get_by_id(test_db, "V001")
    assert vehicle["status"] == "available"
    assert vehicle["rides_since_last_treated"] == 0
    assert vehicle["last_treated_date"] is not None


@pytest.mark.asyncio
async def test_treat_vehicle_not_found(test_db):
    """Test treatment on non-existent vehicle."""
    repo = VehiclesRepository()
    
    result = await repo.treat_vehicle(test_db, "V999", station_id=1)
    
    assert result is False


@pytest.mark.asyncio
async def test_update_vehicle_status(test_db):
    repo = VehiclesRepository()
    
    result = await repo.update_vehicle_status(test_db, "V001", "maintenance")
    
    assert result is True
    vehicle = await repo.get_by_id(test_db, "V001")
    assert vehicle["status"] == "maintenance"


@pytest.mark.asyncio
async def test_update_vehicle_status_not_found(test_db):
    repo = VehiclesRepository()
    
    result = await repo.update_vehicle_status(test_db, "V999", "maintenance")
    
    assert result is False