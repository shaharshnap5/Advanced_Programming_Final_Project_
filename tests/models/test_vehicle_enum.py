"""
Tests for Vehicle models with proper Enum usage for status and type.
Tests verify that all vehicle classes use Vehicle_status and Vehicle_type enums correctly.
"""

from __future__ import annotations

import pytest
import datetime
from src.models.vehicle import (
    Vehicle, VehicleType, VehicleStatus,
    Bicycle, ElectricVehicle, ElectricBicycle, Scooter,
    VehicleFactory
)


# ============================================================================
# Tests for Vehicle_type Enum
# ============================================================================

def test_vehicle_type_enum_values():
    """Test Vehicle_type enum has correct values."""
    assert VehicleType.bike.value == 'bike'
    assert VehicleType.ebike.value == 'ebike'
    assert VehicleType.scooter.value == 'scooter'


def test_vehicle_type_enum_members():
    """Test Vehicle_type enum has all required members."""
    members = [e.name for e in VehicleType]
    assert 'bike' in members
    assert 'ebike' in members
    assert 'scooter' in members


# ============================================================================
# Tests for Vehicle_status Enum
# ============================================================================

def test_vehicle_status_enum_values():
    """Test Vehicle_status enum has correct values."""
    assert VehicleStatus.available.value == 'available'
    assert VehicleStatus.rented.value == 'rented'
    assert VehicleStatus.degraded.value == 'degraded'


def test_vehicle_status_enum_members():
    """Test Vehicle_status enum has all required members."""
    members = [e.name for e in VehicleStatus]
    assert 'available' in members
    assert 'rented' in members
    assert 'degraded' in members


# ============================================================================
# Tests for Bicycle with Enum
# ============================================================================

def test_bicycle_creation_with_enum():
    """Test creating a bicycle with enum types."""
    bike = Bicycle(
        vehicle_id="bike_001",
        station_id=1,
        vehicle_type=VehicleType.bike,
        status=VehicleStatus.available,
        rides_since_last_treated=0,
        last_treated_date=None
    )

    assert bike.vehicle_id == "bike_001"
    assert bike.vehicle_type == VehicleType.bike
    assert bike.status == VehicleStatus.available
    assert isinstance(bike.vehicle_type, VehicleType)
    assert isinstance(bike.status, VehicleStatus)


def test_bicycle_default_vehicle_type():
    """Test that Bicycle has correct default vehicle_type."""
    bike = Bicycle(
        vehicle_id="bike_002",
        station_id=1,
        status=VehicleStatus.available,
        rides_since_last_treated=0,
        last_treated_date=None
    )

    assert bike.vehicle_type == VehicleType.bike


def test_bicycle_rent_sets_status_enum():
    """Test that bicycle rent method sets status to rented enum."""
    bike = Bicycle(
        vehicle_id="bike_003",
        station_id=1,
        vehicle_type=VehicleType.bike,
        status=VehicleStatus.available,
        rides_since_last_treated=0,
        last_treated_date=None
    )

    bike.rent()

    assert bike.status == VehicleStatus.rented
    assert bike.station_id is None
    assert isinstance(bike.status, VehicleStatus)


def test_bicycle_treat_sets_status_enum():
    """Test that bicycle treat method sets status to available enum."""
    bike = Bicycle(
        vehicle_id="bike_004",
        station_id=1,
        vehicle_type=VehicleType.bike,
        status=VehicleStatus.degraded,
        rides_since_last_treated=15,
        last_treated_date=datetime.date(2024, 1, 1)
    )

    bike.treat()

    assert bike.status == VehicleStatus.available
    assert bike.rides_since_last_treated == 0
    assert bike.last_treated_date == datetime.date.today()
    assert isinstance(bike.status, VehicleStatus)


def test_bicycle_return_vehicle_sets_status_enum():
    """Test that bicycle return_vehicle sets status to available enum."""
    bike = Bicycle(
        vehicle_id="bike_005",
        station_id=None,
        vehicle_type=VehicleType.bike,
        status=VehicleStatus.rented,
        rides_since_last_treated=5,
        last_treated_date=None
    )

    bike.return_vehicle(station_id=2)

    assert bike.station_id == 2
    assert bike.status == VehicleStatus.available
    assert isinstance(bike.status, VehicleStatus)


# ============================================================================
# Tests for ElectricBicycle with Enum
# ============================================================================

def test_electric_bicycle_creation_with_enum():
    """Test creating an electric bicycle with enum types."""
    ebike = ElectricBicycle(
        vehicle_id="ebike_001",
        station_id=1,
        vehicle_type=VehicleType.ebike,
        status=VehicleStatus.available,
        rides_since_last_treated=0,
        last_treated_date=None,
        battery_level=100
    )

    assert ebike.vehicle_id == "ebike_001"
    assert ebike.vehicle_type == VehicleType.ebike
    assert ebike.status == VehicleStatus.available
    assert ebike.battery_level == 100
    assert isinstance(ebike.vehicle_type, VehicleType)
    assert isinstance(ebike.status, VehicleStatus)


def test_electric_bicycle_default_vehicle_type():
    """Test that ElectricBicycle has correct default vehicle_type."""
    ebike = ElectricBicycle(
        vehicle_id="ebike_002",
        station_id=1,
        status=VehicleStatus.available,
        rides_since_last_treated=0,
        last_treated_date=None
    )

    assert ebike.vehicle_type == VehicleType.ebike


def test_electric_bicycle_default_battery_level():
    """Test that ElectricBicycle has correct default battery level."""
    ebike = ElectricBicycle(
        vehicle_id="ebike_003",
        station_id=1,
        status=VehicleStatus.available,
        rides_since_last_treated=0,
        last_treated_date=None
    )

    assert ebike.battery_level == 100


def test_electric_bicycle_rent_sets_status_enum():
    """Test that electric bicycle rent sets status to rented enum."""
    ebike = ElectricBicycle(
        vehicle_id="ebike_004",
        station_id=1,
        vehicle_type=VehicleType.ebike,
        status=VehicleStatus.available,
        rides_since_last_treated=0,
        last_treated_date=None,
        battery_level=50
    )

    ebike.rent()

    assert ebike.status == VehicleStatus.rented
    assert isinstance(ebike.status, VehicleStatus)


def test_electric_bicycle_treat_sets_status_enum():
    """Test that electric bicycle treat sets status to available enum."""
    ebike = ElectricBicycle(
        vehicle_id="ebike_005",
        station_id=1,
        vehicle_type=VehicleType.ebike,
        status=VehicleStatus.degraded,
        rides_since_last_treated=15,
        last_treated_date=datetime.date(2024, 1, 1),
        battery_level=10
    )

    ebike.treat()

    assert ebike.status == VehicleStatus.available
    assert ebike.battery_level == 100
    assert ebike.rides_since_last_treated == 0
    assert isinstance(ebike.status, VehicleStatus)


# ============================================================================
# Tests for Scooter with Enum
# ============================================================================

def test_scooter_creation_with_enum():
    """Test creating a scooter with enum types."""
    scooter = Scooter(
        vehicle_id="scooter_001",
        station_id=1,
        vehicle_type=VehicleType.scooter,
        status=VehicleStatus.available,
        rides_since_last_treated=0,
        last_treated_date=None,
        battery_level=100
    )

    assert scooter.vehicle_id == "scooter_001"
    assert scooter.vehicle_type == VehicleType.scooter
    assert scooter.status == VehicleStatus.available
    assert isinstance(scooter.vehicle_type, VehicleType)
    assert isinstance(scooter.status, VehicleStatus)


def test_scooter_default_vehicle_type():
    """Test that Scooter has correct default vehicle_type."""
    scooter = Scooter(
        vehicle_id="scooter_002",
        station_id=1,
        status=VehicleStatus.available,
        rides_since_last_treated=0,
        last_treated_date=None
    )

    assert scooter.vehicle_type == VehicleType.scooter


def test_scooter_rent_sets_status_enum():
    """Test that scooter rent sets status to rented enum."""
    scooter = Scooter(
        vehicle_id="scooter_003",
        station_id=1,
        vehicle_type=VehicleType.scooter,
        status=VehicleStatus.available,
        rides_since_last_treated=0,
        last_treated_date=None,
        battery_level=50
    )

    scooter.rent()

    assert scooter.status == VehicleStatus.rented
    assert isinstance(scooter.status, VehicleStatus)


# ============================================================================
# Tests for VehicleFactory with Enum
# ============================================================================

def test_vehicle_factory_creates_bicycle_with_enum():
    """Test that factory creates bicycle with correct enum types."""
    bike = VehicleFactory.create_vehicle("bike_001", "bike", station_id=1)

    assert isinstance(bike, Bicycle)
    assert bike.vehicle_type == VehicleType.bike
    assert bike.status == VehicleStatus.available
    assert isinstance(bike.vehicle_type, VehicleType)
    assert isinstance(bike.status, VehicleStatus)


def test_vehicle_factory_creates_electric_bicycle_with_enum():
    """Test that factory creates electric bicycle with correct enum types."""
    ebike = VehicleFactory.create_vehicle("ebike_001", "ebike", station_id=1)

    assert isinstance(ebike, ElectricBicycle)
    assert ebike.vehicle_type == VehicleType.ebike
    assert ebike.status == VehicleStatus.available
    assert isinstance(ebike.vehicle_type, VehicleType)
    assert isinstance(ebike.status, VehicleStatus)


def test_vehicle_factory_creates_scooter_with_enum():
    """Test that factory creates scooter with correct enum types."""
    scooter = VehicleFactory.create_vehicle("scooter_001", "scooter", station_id=1)

    assert isinstance(scooter, Scooter)
    assert scooter.vehicle_type == VehicleType.scooter
    assert scooter.status == VehicleStatus.available
    assert isinstance(scooter.vehicle_type, VehicleType)
    assert isinstance(scooter.status, VehicleStatus)


def test_vehicle_factory_case_insensitive():
    """Test that factory handles case-insensitive vehicle type input."""
    bike1 = VehicleFactory.create_vehicle("bike_001", "bike")
    bike2 = VehicleFactory.create_vehicle("bike_002", "BIKE")
    bike3 = VehicleFactory.create_vehicle("bike_003", "Bike")

    assert bike1.vehicle_type == bike2.vehicle_type == bike3.vehicle_type == VehicleType.bike
    assert isinstance(bike1.vehicle_type, VehicleType)


def test_vehicle_factory_without_station_id():
    """Test that factory creates vehicles without station_id."""
    bike = VehicleFactory.create_vehicle("bike_001", "bike")

    assert bike.station_id is None
    assert bike.vehicle_type == VehicleType.bike
    assert bike.status == VehicleStatus.available


# ============================================================================
# Tests for Enum Comparisons
# ============================================================================

def test_vehicle_status_enum_comparison():
    """Test comparing vehicle status with enum."""
    bike = Bicycle(
        vehicle_id="bike_001",
        station_id=1,
        vehicle_type=VehicleType.bike,
        status=VehicleStatus.available,
        rides_since_last_treated=0,
        last_treated_date=None
    )

    # Should be able to compare directly with enum
    assert bike.status == VehicleStatus.available
    assert bike.status != VehicleStatus.rented
    assert bike.status != VehicleStatus.degraded


def test_vehicle_type_enum_comparison():
    """Test comparing vehicle type with enum."""
    bike = Bicycle(
        vehicle_id="bike_001",
        station_id=1,
        vehicle_type=VehicleType.bike,
        status=VehicleStatus.available,
        rides_since_last_treated=0,
        last_treated_date=None
    )

    # Should be able to compare directly with enum
    assert bike.vehicle_type == VehicleType.bike
    assert bike.vehicle_type != VehicleType.ebike
    assert bike.vehicle_type != VehicleType.scooter


# ============================================================================
# Tests for Enum in Return Vehicle
# ============================================================================

def test_return_vehicle_degradation_uses_enum():
    """Test that return_vehicle correctly uses status enum."""
    bike = Bicycle(
        vehicle_id="bike_001",
        station_id=None,
        vehicle_type=VehicleType.bike,
        status=VehicleStatus.rented,
        rides_since_last_treated=15,  # More than 10
        last_treated_date=None
    )

    bike.return_vehicle(station_id=1)

    # Should be degraded because rides_since_last_treated > 10
    assert bike.status == VehicleStatus.degraded
    assert isinstance(bike.status, VehicleStatus)
    assert bike.station_id == 1


def test_return_vehicle_no_degradation_uses_enum():
    """Test that return_vehicle sets available when rides <= 10."""
    bike = Bicycle(
        vehicle_id="bike_001",
        station_id=None,
        vehicle_type=VehicleType.bike,
        status=VehicleStatus.rented,
        rides_since_last_treated=5,  # Less than or equal to 10
        last_treated_date=None
    )

    bike.return_vehicle(station_id=1)

    # Should be available because rides_since_last_treated <= 10
    assert bike.status == VehicleStatus.available
    assert isinstance(bike.status, VehicleStatus)
    assert bike.station_id == 1


# ============================================================================
# Tests for Report Degraded with Enum
# ============================================================================

def test_report_degraded_uses_enum():
    """Test that report_degraded sets status to degraded enum."""
    bike = Bicycle(
        vehicle_id="bike_001",
        station_id=1,
        vehicle_type=VehicleType.bike,
        status=VehicleStatus.available,
        rides_since_last_treated=0,
        last_treated_date=None
    )

    bike.report_degraded()

    assert bike.status == VehicleStatus.degraded
    assert isinstance(bike.status, VehicleStatus)

