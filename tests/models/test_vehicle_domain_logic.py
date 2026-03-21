from __future__ import annotations

from datetime import date

from src.models.vehicle import Bicycle, ElectricBicycle, VehicleStatus, VehicleType


def test_return_vehicle_marks_vehicle_degraded_after_more_than_ten_rides():
    bike = Bicycle(
        vehicle_id="BIKE001",
        station_id=None,
        vehicle_type=VehicleType.bike,
        status=VehicleStatus.rented,
        rides_since_last_treated=11,
        last_treated_date=date(2025, 1, 1),
    )

    bike.return_vehicle(station_id=2)

    assert bike.station_id == 2
    assert bike.status == VehicleStatus.degraded


def test_return_vehicle_marks_vehicle_available_when_ride_count_not_over_threshold():
    bike = Bicycle(
        vehicle_id="BIKE002",
        station_id=None,
        vehicle_type=VehicleType.bike,
        status=VehicleStatus.rented,
        rides_since_last_treated=10,
        last_treated_date=date(2025, 1, 1),
    )

    bike.return_vehicle(station_id=1)

    assert bike.station_id == 1
    assert bike.status == VehicleStatus.available


def test_bicycle_treat_resets_maintenance_fields():
    bike = Bicycle(
        vehicle_id="BIKE003",
        station_id=1,
        vehicle_type=VehicleType.bike,
        status=VehicleStatus.degraded,
        rides_since_last_treated=15,
        last_treated_date=date(2024, 1, 1),
    )

    bike.treat()

    assert bike.status == VehicleStatus.available
    assert bike.rides_since_last_treated == 0
    assert bike.last_treated_date == date.today()


def test_electric_vehicle_treat_also_recharges_battery():
    ebike = ElectricBicycle(
        vehicle_id="EBIKE001",
        station_id=1,
        vehicle_type=VehicleType.ebike,
        status=VehicleStatus.degraded,
        rides_since_last_treated=12,
        last_treated_date=date(2024, 1, 1),
        battery_level=15,
    )

    ebike.treat()

    assert ebike.status == VehicleStatus.available
    assert ebike.rides_since_last_treated == 0
    assert ebike.last_treated_date == date.today()
    assert ebike.battery_level == 100
