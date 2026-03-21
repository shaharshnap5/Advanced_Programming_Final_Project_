from __future__ import annotations

import pytest

from src.repositories.vehicles_repository import VehiclesRepository
from src.models.vehicle import VehicleType, VehicleStatus, Vehicle


@pytest.mark.asyncio
async def test_get_by_id(test_db):
    repo = VehiclesRepository()
    
    vehicle = await repo.get_by_id(test_db, "V001")
    
    assert vehicle is not None
    assert isinstance(vehicle, Vehicle)
    assert vehicle.vehicle_id == "V001"
    assert vehicle.station_id == 1
    assert vehicle.vehicle_type == VehicleType.bicycle
    assert vehicle.status == VehicleStatus.available
    assert vehicle.rides_since_last_treated == 5


@pytest.mark.asyncio
async def test_get_by_id_not_found(test_db):
    repo = VehiclesRepository()
    
    vehicle = await repo.get_by_id(test_db, "V999")
    
    assert vehicle is None


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
    assert vehicle.status == VehicleStatus.available
    assert vehicle.rides_since_last_treated == 0
    assert vehicle.last_treated_date is not None


@pytest.mark.asyncio
async def test_treat_vehicle_not_found(test_db):
    """Test treatment on non-existent vehicle."""
    repo = VehiclesRepository()
    
    result = await repo.treat_vehicle(test_db, "V999", station_id=1)
    
    assert result is False


@pytest.mark.asyncio
async def test_mark_vehicle_degraded_and_detach(test_db):
    repo = VehiclesRepository()

    result = await repo.mark_vehicle_degraded_and_detach(test_db, "V001")

    assert result is True
    vehicle = await repo.get_by_id(test_db, "V001")
    assert vehicle is not None
    assert vehicle.status == VehicleStatus.degraded
    assert vehicle.station_id is None
