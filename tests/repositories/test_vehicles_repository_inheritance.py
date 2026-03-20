from __future__ import annotations

import pytest

from src.models.vehicle import Bicycle, ElectricBicycle, Scooter, VehicleStatus, VehicleType
from src.repositories.vehicles_repository import VehiclesRepository


@pytest.mark.asyncio
async def test_schema_uses_child_tables_for_battery(test_db):
    cursor = await test_db.execute("PRAGMA table_info(vehicles)")
    vehicles_columns = [row[1] for row in await cursor.fetchall()]
    await cursor.close()

    assert "battery" not in vehicles_columns

    cursor = await test_db.execute("PRAGMA table_info(scooters)")
    scooter_columns = [row[1] for row in await cursor.fetchall()]
    await cursor.close()

    assert "battery" in scooter_columns


@pytest.mark.asyncio
async def test_get_by_id_joins_scooter_battery_from_child_table(test_db):
    repo = VehiclesRepository()

    vehicle = await repo.get_by_id(test_db, "V002")

    assert vehicle is not None
    assert vehicle.vehicle_type == VehicleType.scooter
    assert vehicle.battery == 100


@pytest.mark.asyncio
async def test_dock_vehicle_updates_scooter_battery_in_child_table(test_db):
    repo = VehiclesRepository()

    await test_db.execute(
        "UPDATE vehicles SET status = 'rented', station_id = NULL, rides_since_last_treated = 2 WHERE vehicle_id = 'V002'"
    )
    await test_db.execute("UPDATE scooters SET battery = 100 WHERE vehicle_id = 'V002'")
    await test_db.commit()

    updated = await repo.dock_vehicle(test_db, "V002", station_id=2)

    assert updated is not None
    assert isinstance(updated, Scooter)
    assert updated.battery == 86

    cursor = await test_db.execute("SELECT battery FROM scooters WHERE vehicle_id = 'V002'")
    row = await cursor.fetchone()
    await cursor.close()
    assert row[0] == 86


@pytest.mark.asyncio
async def test_treat_vehicle_recharges_ev_in_child_table(test_db):
    repo = VehiclesRepository()

    await test_db.execute(
        "UPDATE vehicles SET status = 'degraded', rides_since_last_treated = 8 WHERE vehicle_id = 'V002'"
    )
    await test_db.execute("UPDATE scooters SET battery = 13 WHERE vehicle_id = 'V002'")
    await test_db.commit()

    success = await repo.treat_vehicle(test_db, "V002", station_id=1)
    assert success is True

    treated = await repo.get_by_id(test_db, "V002")
    assert treated is not None
    assert treated.status == VehicleStatus.available
    assert treated.rides_since_last_treated == 0
    assert treated.battery == 100


@pytest.mark.asyncio
async def test_create_vehicle_inserts_base_and_matching_child_rows(test_db):
    repo = VehiclesRepository()

    ebike = ElectricBicycle(
        vehicle_id="E_CREATE_001",
        station_id=1,
        vehicle_type=VehicleType.ebike,
        status=VehicleStatus.available,
        rides_since_last_treated=0,
        last_treated_date=None,
        battery=91,
    )
    bike = Bicycle(
        vehicle_id="B_CREATE_001",
        station_id=1,
        vehicle_type=VehicleType.bike,
        status=VehicleStatus.available,
        rides_since_last_treated=0,
        last_treated_date=None,
        battery=None,
    )

    created_ebike = await repo.create_vehicle(test_db, ebike)
    created_bike = await repo.create_vehicle(test_db, bike)

    assert isinstance(created_ebike, ElectricBicycle)
    assert created_ebike.battery == 91
    assert isinstance(created_bike, Bicycle)
    assert created_bike.battery is None

    cursor = await test_db.execute("SELECT battery FROM ebikes WHERE vehicle_id = 'E_CREATE_001'")
    ebike_row = await cursor.fetchone()
    await cursor.close()
    assert ebike_row[0] == 91

    cursor = await test_db.execute("SELECT COUNT(*) FROM scooters WHERE vehicle_id = 'B_CREATE_001'")
    scooter_count = await cursor.fetchone()
    await cursor.close()
    assert scooter_count[0] == 0

    cursor = await test_db.execute("SELECT COUNT(*) FROM ebikes WHERE vehicle_id = 'B_CREATE_001'")
    ebike_count = await cursor.fetchone()
    await cursor.close()
    assert ebike_count[0] == 0
