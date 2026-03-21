from __future__ import annotations

from datetime import date

import pytest

from src.models.vehicle import Bicycle, ElectricBicycle, Scooter, VehicleStatus, VehicleType



def test_bicycle_return_vehicle_does_not_use_battery_logic():
	bicycle = Bicycle(
		vehicle_id="bicycle_POLY_001",
		station_id=None,
		vehicle_type=VehicleType.bicycle,
		status=VehicleStatus.rented,
		rides_since_last_treated=0,
		last_treated_date=None,
		battery=None,
	)

	bicycle.return_vehicle(station_id=1)

	assert bicycle.station_id == 1
	assert bicycle.status == VehicleStatus.available
	assert bicycle.rides_since_last_treated == 1
	assert bicycle.battery is None


def test_electric_bicycle_end_ride_drains_exactly_14_percent():
	electric_bicycle = ElectricBicycle(
		vehicle_id="electric_bicycle_POLY_001",
		station_id=None,
		vehicle_type=VehicleType.electric_bicycle,
		status=VehicleStatus.rented,
		rides_since_last_treated=2,
		last_treated_date=date.today(),
		battery=100,
	)

	electric_bicycle.return_vehicle(station_id=3)

	assert electric_bicycle.rides_since_last_treated == 3
	assert electric_bicycle.battery == 86
	assert electric_bicycle.status == VehicleStatus.available


def test_scooter_cannot_rent_below_14_battery():
	scooter = Scooter(
		vehicle_id="SCOOTER_POLY_001",
		station_id=2,
		vehicle_type=VehicleType.scooter,
		status=VehicleStatus.available,
		rides_since_last_treated=0,
		last_treated_date=None,
		battery=13,
	)

	with pytest.raises(Exception, match="Electric vehicle is not available for rent"):
		scooter.rent()


def test_electric_vehicle_treatment_recharges_to_100():
	scooter = Scooter(
		vehicle_id="SCOOTER_POLY_002",
		station_id=2,
		vehicle_type=VehicleType.scooter,
		status=VehicleStatus.degraded,
		rides_since_last_treated=9,
		last_treated_date=date(2025, 1, 1),
		battery=22,
	)

	scooter.treat()

	assert scooter.status == VehicleStatus.available
	assert scooter.rides_since_last_treated == 0
	assert scooter.battery == 100
