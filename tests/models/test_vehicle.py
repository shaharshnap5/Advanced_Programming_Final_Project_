from __future__ import annotations

from datetime import date

import pytest

from src.models.vehicle import Bike, EBike, Scooter, VehicleStatus, VehicleType


def test_bike_return_vehicle_does_not_use_battery_logic():
	bike = Bike(
		vehicle_id="BIKE_POLY_001",
		station_id=None,
		vehicle_type=VehicleType.bike,
		status=VehicleStatus.rented,
		rides_since_last_treated=0,
		last_treated_date=None,
		battery=None,
	)

	bike.return_vehicle(station_id=1)

	assert bike.station_id == 1
	assert bike.status == VehicleStatus.available
	assert bike.rides_since_last_treated == 1
	assert bike.battery is None


def test_ebike_end_ride_drains_exactly_14_percent():
	ebike = EBike(
		vehicle_id="EBIKE_POLY_001",
		station_id=None,
		vehicle_type=VehicleType.ebike,
		status=VehicleStatus.rented,
		rides_since_last_treated=2,
		last_treated_date=date.today(),
		battery=100,
	)

	ebike.return_vehicle(station_id=3)

	assert ebike.rides_since_last_treated == 3
	assert ebike.battery == 86
	assert ebike.status == VehicleStatus.available


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
