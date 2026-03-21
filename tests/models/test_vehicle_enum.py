"""
Tests for Vehicle models with proper Enum usage for status and type.
Tests verify that all vehicle classes use Vehicle_status and Vehicle_type enums correctly.
"""

from __future__ import annotations

import datetime
from src.models.vehicle import (
    VehicleType,
    VehicleStatus,
    Bicycle,
    ElectricBicycle,
    Scooter,
    VehicleFactory,
)

# ============================================================================
# Tests for Vehicle_type Enum
# ============================================================================


def test_vehicle_type_enum_values():
    """Test Vehicle_type enum has correct values."""
    assert VehicleType.bicycle.value == "bicycle"
    assert VehicleType.electric_bicycle.value == "electric_bicycle"
    assert VehicleType.scooter.value == "scooter"


def test_vehicle_type_enum_members():
    """Test Vehicle_type enum has all required members."""
    members = [e.name for e in VehicleType]
    assert "bicycle" in members
    assert "electric_bicycle" in members
    assert "scooter" in members


# ============================================================================
# Tests for Vehicle_status Enum
# ============================================================================


def test_vehicle_status_enum_values():
    """Test Vehicle_status enum has correct values."""
    assert VehicleStatus.available.value == "available"
    assert VehicleStatus.rented.value == "rented"
    assert VehicleStatus.degraded.value == "degraded"


def test_vehicle_status_enum_members():
    """Test Vehicle_status enum has all required members."""
    members = [e.name for e in VehicleStatus]
    assert "available" in members
    assert "rented" in members
    assert "degraded" in members


# ============================================================================
# Tests for Bicycle with Enum
# ============================================================================


def test_bicycle_creation_with_enum():
    """Test creating a bicycle with enum types."""
    bicycle = Bicycle(
        vehicle_id="bicycle_001",
        station_id=1,
        vehicle_type=VehicleType.bicycle,
        status=VehicleStatus.available,
        rides_since_last_treated=0,
        last_treated_date=None,
    )

    assert bicycle.vehicle_id == "bicycle_001"
    assert bicycle.vehicle_type == VehicleType.bicycle
    assert bicycle.status == VehicleStatus.available
    assert isinstance(bicycle.vehicle_type, VehicleType)
    assert isinstance(bicycle.status, VehicleStatus)


def test_bicycle_default_vehicle_type():
    """Test that Bicycle has correct default vehicle_type."""
    bicycle = Bicycle(
        vehicle_id="bicycle_002",
        station_id=1,
        status=VehicleStatus.available,
        rides_since_last_treated=0,
        last_treated_date=None,
    )

    assert bicycle.vehicle_type == VehicleType.bicycle


def test_bicycle_rent_sets_status_enum():
    """Test that bicycle rent method sets status to rented enum."""
    bicycle = Bicycle(
        vehicle_id="bicycle_003",
        station_id=1,
        vehicle_type=VehicleType.bicycle,
        status=VehicleStatus.available,
        rides_since_last_treated=0,
        last_treated_date=None,
    )

    bicycle.rent()

    assert bicycle.status == VehicleStatus.rented
    assert bicycle.station_id is None
    assert isinstance(bicycle.status, VehicleStatus)


def test_bicycle_treat_sets_status_enum():
    """Test that bicycle treat method sets status to available enum."""
    bicycle = Bicycle(
        vehicle_id="bicycle_004",
        station_id=1,
        vehicle_type=VehicleType.bicycle,
        status=VehicleStatus.degraded,
        rides_since_last_treated=15,
        last_treated_date=datetime.date(2024, 1, 1),
    )

    bicycle.treat()

    assert bicycle.status == VehicleStatus.available
    assert bicycle.rides_since_last_treated == 0
    assert bicycle.last_treated_date == datetime.date.today()
    assert isinstance(bicycle.status, VehicleStatus)


def test_bicycle_return_vehicle_sets_status_enum():
    """Test that bicycle return_vehicle sets status to available enum."""
    bicycle = Bicycle(
        vehicle_id="bicycle_005",
        station_id=None,
        vehicle_type=VehicleType.bicycle,
        status=VehicleStatus.rented,
        rides_since_last_treated=5,
        last_treated_date=None,
    )

    bicycle.return_vehicle(station_id=2)

    assert bicycle.station_id == 2
    assert bicycle.status == VehicleStatus.available
    assert isinstance(bicycle.status, VehicleStatus)


# ============================================================================
# Tests for ElectricBicycle with Enum
# ============================================================================


def test_electric_bicycle_creation_with_enum():
    """Test creating an electric bicycle with enum types."""
    electric_bicycle = ElectricBicycle(
        vehicle_id="electric_bicycle_001",
        station_id=1,
        vehicle_type=VehicleType.electric_bicycle,
        status=VehicleStatus.available,
        rides_since_last_treated=0,
        last_treated_date=None,
        battery_level=100,
    )

    assert electric_bicycle.vehicle_id == "electric_bicycle_001"
    assert electric_bicycle.vehicle_type == VehicleType.electric_bicycle
    assert electric_bicycle.status == VehicleStatus.available
    assert electric_bicycle.battery_level == 100
    assert isinstance(electric_bicycle.vehicle_type, VehicleType)
    assert isinstance(electric_bicycle.status, VehicleStatus)


def test_electric_bicycle_default_vehicle_type():
    """Test that ElectricBicycle has correct default vehicle_type."""
    electric_bicycle = ElectricBicycle(
        vehicle_id="electric_bicycle_002",
        station_id=1,
        status=VehicleStatus.available,
        rides_since_last_treated=0,
        last_treated_date=None,
    )

    assert electric_bicycle.vehicle_type == VehicleType.electric_bicycle


def test_electric_bicycle_default_battery_level():
    """Test that ElectricBicycle has correct default battery level."""
    electric_bicycle = ElectricBicycle(
        vehicle_id="electric_bicycle_003",
        station_id=1,
        status=VehicleStatus.available,
        rides_since_last_treated=0,
        last_treated_date=None,
    )

    assert electric_bicycle.battery_level == 100


def test_electric_bicycle_rent_sets_status_enum():
    """Test that electric bicycle rent sets status to rented enum."""
    electric_bicycle = ElectricBicycle(
        vehicle_id="electric_bicycle_004",
        station_id=1,
        vehicle_type=VehicleType.electric_bicycle,
        status=VehicleStatus.available,
        rides_since_last_treated=0,
        last_treated_date=None,
        battery_level=50,
    )

    electric_bicycle.rent()

    assert electric_bicycle.status == VehicleStatus.rented
    assert isinstance(electric_bicycle.status, VehicleStatus)


def test_electric_bicycle_treat_sets_status_enum():
    """Test that electric bicycle treat sets status to available enum."""
    electric_bicycle = ElectricBicycle(
        vehicle_id="electric_bicycle_005",
        station_id=1,
        vehicle_type=VehicleType.electric_bicycle,
        status=VehicleStatus.degraded,
        rides_since_last_treated=15,
        last_treated_date=datetime.date(2024, 1, 1),
        battery_level=10,
    )

    electric_bicycle.treat()

    assert electric_bicycle.status == VehicleStatus.available
    assert electric_bicycle.battery_level == 100
    assert electric_bicycle.rides_since_last_treated == 0
    assert isinstance(electric_bicycle.status, VehicleStatus)


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
        battery_level=100,
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
        last_treated_date=None,
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
        battery_level=50,
    )

    scooter.rent()

    assert scooter.status == VehicleStatus.rented
    assert isinstance(scooter.status, VehicleStatus)


# ============================================================================
# Tests for VehicleFactory with Enum
# ============================================================================


def test_vehicle_factory_creates_bicycle_with_enum():
    """Test that factory creates bicycle with correct enum types."""
    bicycle = VehicleFactory.create_vehicle("bicycle_001", "bicycle", station_id=1)

    assert isinstance(bicycle, Bicycle)
    assert bicycle.vehicle_type == VehicleType.bicycle
    assert bicycle.status == VehicleStatus.available
    assert isinstance(bicycle.vehicle_type, VehicleType)
    assert isinstance(bicycle.status, VehicleStatus)


def test_vehicle_factory_creates_electric_bicycle_with_enum():
    """Test that factory creates electric bicycle with correct enum types."""
    electric_bicycle = VehicleFactory.create_vehicle(
        "electric_bicycle_001", "electric_bicycle", station_id=1
    )

    assert isinstance(electric_bicycle, ElectricBicycle)
    assert electric_bicycle.vehicle_type == VehicleType.electric_bicycle
    assert electric_bicycle.status == VehicleStatus.available
    assert isinstance(electric_bicycle.vehicle_type, VehicleType)
    assert isinstance(electric_bicycle.status, VehicleStatus)


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
    bicycle1 = VehicleFactory.create_vehicle("bicycle_001", "bicycle")
    bicycle2 = VehicleFactory.create_vehicle("bicycle_002", "BICYCLE")
    bicycle3 = VehicleFactory.create_vehicle("bicycle_003", "Bicycle")

    assert (
        bicycle1.vehicle_type
        == bicycle2.vehicle_type
        == bicycle3.vehicle_type
        == VehicleType.bicycle
    )
    assert isinstance(bicycle1.vehicle_type, VehicleType)


def test_vehicle_factory_without_station_id():
    """Test that factory creates vehicles without station_id."""
    bicycle = VehicleFactory.create_vehicle("bicycle_001", "bicycle")

    assert bicycle.station_id is None
    assert bicycle.vehicle_type == VehicleType.bicycle
    assert bicycle.status == VehicleStatus.available


# ============================================================================
# Tests for Enum Comparisons
# ============================================================================


def test_vehicle_status_enum_comparison():
    """Test comparing vehicle status with enum."""
    bicycle = Bicycle(
        vehicle_id="bicycle_001",
        station_id=1,
        vehicle_type=VehicleType.bicycle,
        status=VehicleStatus.available,
        rides_since_last_treated=0,
        last_treated_date=None,
    )

    # Should be able to compare directly with enum
    assert bicycle.status == VehicleStatus.available
    assert bicycle.status != VehicleStatus.rented
    assert bicycle.status != VehicleStatus.degraded


def test_vehicle_type_enum_comparison():
    """Test comparing vehicle type with enum."""
    bicycle = Bicycle(
        vehicle_id="bicycle_001",
        station_id=1,
        vehicle_type=VehicleType.bicycle,
        status=VehicleStatus.available,
        rides_since_last_treated=0,
        last_treated_date=None,
    )

    # Should be able to compare directly with enum
    assert bicycle.vehicle_type == VehicleType.bicycle
    assert bicycle.vehicle_type != VehicleType.electric_bicycle
    assert bicycle.vehicle_type != VehicleType.scooter


# ============================================================================
# Tests for Enum in Return Vehicle
# ============================================================================


def test_return_vehicle_degradation_uses_enum():
    """Test that return_vehicle correctly uses status enum."""
    bicycle = Bicycle(
        vehicle_id="bicycle_001",
        station_id=None,
        vehicle_type=VehicleType.bicycle,
        status=VehicleStatus.rented,
        rides_since_last_treated=15,  # More than 10
        last_treated_date=None,
    )

    bicycle.return_vehicle(station_id=1)

    # Should be degraded because rides_since_last_treated > 10
    assert bicycle.status == VehicleStatus.degraded
    assert isinstance(bicycle.status, VehicleStatus)
    assert bicycle.station_id == 1


def test_return_vehicle_no_degradation_uses_enum():
    """Test that return_vehicle sets available when rides <= 10."""
    bicycle = Bicycle(
        vehicle_id="bicycle_001",
        station_id=None,
        vehicle_type=VehicleType.bicycle,
        status=VehicleStatus.rented,
        rides_since_last_treated=5,  # Less than or equal to 10
        last_treated_date=None,
    )

    bicycle.return_vehicle(station_id=1)

    # Should be available because rides_since_last_treated <= 10
    assert bicycle.status == VehicleStatus.available
    assert isinstance(bicycle.status, VehicleStatus)
    assert bicycle.station_id == 1


# ============================================================================
# Tests for Report Degraded with Enum
# ============================================================================


def test_report_degraded_uses_enum():
    """Test that report_degraded sets status to degraded enum."""
    bicycle = Bicycle(
        vehicle_id="bicycle_001",
        station_id=1,
        vehicle_type=VehicleType.bicycle,
        status=VehicleStatus.available,
        rides_since_last_treated=0,
        last_treated_date=None,
    )

    bicycle.report_degraded()

    assert bicycle.status == VehicleStatus.degraded
    assert isinstance(bicycle.status, VehicleStatus)
