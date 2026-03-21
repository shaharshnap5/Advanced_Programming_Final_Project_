from __future__ import annotations

from datetime import date

from src.models.vehicle import Bicycle, ElectricBicycle, VehicleStatus, VehicleType


def test_bicycle_degrades_after_exceeding_maintenance_threshold_on_return():
    bicycle = Bicycle(
        vehicle_id="BICYCLE_MAINT_001",
        station_id=None,
        vehicle_type=VehicleType.bicycle,
        status=VehicleStatus.rented,
        rides_since_last_treated=10,
        last_treated_date=date(2026, 1, 1),
    )

    bicycle.return_vehicle(station_id=1)

    assert bicycle.rides_since_last_treated == 11
    assert bicycle.status == VehicleStatus.degraded
    assert bicycle.station_id == 1


def test_electric_bicycle_treat_resets_status_and_recharges_battery():
    electric_bicycle = ElectricBicycle(
        vehicle_id="ELECTRIC_BICYCLE_MAINT_001",
        station_id=2,
        vehicle_type=VehicleType.electric_bicycle,
        status=VehicleStatus.degraded,
        rides_since_last_treated=8,
        last_treated_date=date(2026, 1, 1),
        battery=22,
    )

    electric_bicycle.treat()

    assert electric_bicycle.status == VehicleStatus.available
    assert electric_bicycle.rides_since_last_treated == 0
    assert electric_bicycle.battery == 100
