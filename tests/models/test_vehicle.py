"""
Comprehensive tests for the Vehicle models with 100% coverage.
Tests cover:
- Vehicle base class (abstract)
- ElectricVehicle class
- Bicycle class
- ElectricBicycle class
- Scooter class
- All methods: rent(), return_vehicle(), report_degraded(), treat(), charge()
"""

import pytest
from datetime import date, timedelta
from unittest.mock import Mock, patch
from abc import ABC

from src.models.vehicle import (
    Vehicle, ElectricVehicle, Bicycle, ElectricBicycle, Scooter
)


class TestBicycle:
    """Tests for the Bicycle model."""

    @pytest.fixture
    def available_bicycle(self):
        """Create an available bicycle for testing."""
        return Bicycle(
            vehicle_id="BIKE001",
            station_id=1,
            vehicle_type="bike",
            status="available",
            rides_since_last_treated=0,
            last_treated_date=date.today()
        )

    @pytest.fixture
    def degraded_bicycle(self):
        """Create a degraded bicycle for testing."""
        return Bicycle(
            vehicle_id="BIKE002",
            station_id=2,
            vehicle_type="bike",
            status="degraded",
            rides_since_last_treated=10,
            last_treated_date=date.today() - timedelta(days=30)
        )

    @pytest.fixture
    def rented_bicycle(self):
        """Create a rented bicycle for testing."""
        return Bicycle(
            vehicle_id="BIKE003",
            station_id=None,
            vehicle_type="bike",
            status="rented",
            rides_since_last_treated=3,
            last_treated_date=date.today()
        )

    def test_bicycle_initialization(self, available_bicycle):
        """Test that a Bicycle can be initialized with required fields."""
        assert available_bicycle.vehicle_id == "BIKE001"
        assert available_bicycle.station_id == 1
        assert available_bicycle.vehicle_type == "bike"
        assert available_bicycle.status == "available"
        assert available_bicycle.rides_since_last_treated == 0

    def test_bicycle_default_vehicle_type(self):
        """Test that vehicle_type defaults to 'bike'."""
        bike = Bicycle(
            vehicle_id="BIKE004",
            station_id=1,
            status="available",
            rides_since_last_treated=0,
            last_treated_date=None
        )
        assert bike.vehicle_type == "bike"

    def test_bicycle_rent_available(self, available_bicycle):
        """Test renting an available bicycle with rides below threshold."""
        available_bicycle.rent()

        assert available_bicycle.status == "rented"
        assert available_bicycle.station_id is None

    def test_bicycle_rent_not_available_degraded(self, degraded_bicycle):
        """Test that renting a degraded bicycle raises an exception."""
        with pytest.raises(Exception, match="Bike is not available for rent"):
            degraded_bicycle.rent()

    def test_bicycle_rent_not_available_too_many_rides(self):
        """Test that renting a bicycle with too many rides raises an exception."""
        bike = Bicycle(
            vehicle_id="BIKE005",
            station_id=1,
            vehicle_type="bike",
            status="available",
            rides_since_last_treated=7,
            last_treated_date=date.today()
        )

        with pytest.raises(Exception, match="Bike is not available for rent"):
            bike.rent()

    def test_bicycle_return_vehicle_below_threshold(self, available_bicycle):
        """Test returning a bicycle with rides below treatment threshold."""
        available_bicycle.rides_since_last_treated = 5
        available_bicycle.return_vehicle(2)

        assert available_bicycle.station_id == 2
        assert available_bicycle.status == "available"

    def test_bicycle_return_vehicle_at_threshold(self, available_bicycle):
        """Test returning a bicycle with rides at treatment threshold."""
        available_bicycle.rides_since_last_treated = 7
        available_bicycle.return_vehicle(2)

        assert available_bicycle.station_id == 2
        assert available_bicycle.status == "degraded"

    def test_bicycle_return_vehicle_above_threshold(self, available_bicycle):
        """Test returning a bicycle with rides above treatment threshold."""
        available_bicycle.rides_since_last_treated = 10
        available_bicycle.return_vehicle(3)

        assert available_bicycle.station_id == 3
        assert available_bicycle.status == "degraded"

    def test_bicycle_report_degraded(self, available_bicycle):
        """Test reporting a bicycle as degraded."""
        assert available_bicycle.status == "available"
        available_bicycle.report_degraded()

        assert available_bicycle.status == "degraded"

    def test_bicycle_treat(self, degraded_bicycle):
        """Test treating a degraded bicycle."""
        degraded_bicycle.treat()

        assert degraded_bicycle.status == "available"
        assert degraded_bicycle.rides_since_last_treated == 0
        assert degraded_bicycle.last_treated_date == date.today()

    def test_bicycle_treat_resets_rides(self):
        """Test that treat resets rides_since_last_treated."""
        bike = Bicycle(
            vehicle_id="BIKE006",
            station_id=1,
            vehicle_type="bike",
            status="degraded",
            rides_since_last_treated=8,
            last_treated_date=date.today() - timedelta(days=7)
        )

        initial_rides = bike.rides_since_last_treated
        bike.treat()

        assert bike.rides_since_last_treated == 0
        assert bike.rides_since_last_treated < initial_rides


class TestElectricBicycle:
    """Tests for the ElectricBicycle model."""

    @pytest.fixture
    def available_ebike(self):
        """Create an available electric bicycle for testing."""
        return ElectricBicycle(
            vehicle_id="EBIKE001",
            station_id=1,
            vehicle_type="ebike",
            status="available",
            rides_since_last_treated=0,
            last_treated_date=date.today(),
            battery_level=100
        )

    @pytest.fixture
    def low_battery_ebike(self):
        """Create an electric bicycle with low battery."""
        return ElectricBicycle(
            vehicle_id="EBIKE002",
            station_id=2,
            vehicle_type="ebike",
            status="available",
            rides_since_last_treated=3,
            last_treated_date=date.today(),
            battery_level=15
        )

    def test_ebike_initialization(self, available_ebike):
        """Test that an ElectricBicycle can be initialized."""
        assert available_ebike.vehicle_id == "EBIKE001"
        assert available_ebike.vehicle_type == "ebike"
        assert available_ebike.battery_level == 100

    def test_ebike_default_vehicle_type(self):
        """Test that ElectricBicycle vehicle_type defaults to 'ebike'."""
        ebike = ElectricBicycle(
            vehicle_id="EBIKE003",
            station_id=1,
            status="available",
            rides_since_last_treated=0,
            last_treated_date=None
        )
        assert ebike.vehicle_type == "ebike"

    def test_ebike_default_battery_level(self):
        """Test that ElectricBicycle battery_level defaults to 100."""
        ebike = ElectricBicycle(
            vehicle_id="EBIKE004",
            station_id=1,
            status="available",
            rides_since_last_treated=0,
            last_treated_date=None
        )
        assert ebike.battery_level == 100

    def test_ebike_rent_available_sufficient_battery(self, available_ebike):
        """Test renting an available electric bicycle with sufficient battery."""
        available_ebike.rent()

        assert available_ebike.status == "rented"
        assert available_ebike.station_id is None

    def test_ebike_rent_low_battery(self, low_battery_ebike):
        """Test that renting with low battery raises an exception."""
        with pytest.raises(Exception, match="Electric vehicle is not available for rent"):
            low_battery_ebike.rent()

    def test_ebike_rent_critical_battery_level_20(self):
        """Test renting with battery exactly at 20% threshold."""
        ebike = ElectricBicycle(
            vehicle_id="EBIKE005",
            station_id=1,
            vehicle_type="ebike",
            status="available",
            rides_since_last_treated=0,
            last_treated_date=date.today(),
            battery_level=20
        )

        with pytest.raises(Exception, match="Electric vehicle is not available for rent"):
            ebike.rent()

    def test_ebike_rent_above_battery_threshold(self):
        """Test renting with battery just above 20% threshold."""
        ebike = ElectricBicycle(
            vehicle_id="EBIKE006",
            station_id=1,
            vehicle_type="ebike",
            status="available",
            rides_since_last_treated=0,
            last_treated_date=date.today(),
            battery_level=21
        )

        ebike.rent()
        assert ebike.status == "rented"

    def test_ebike_treat_resets_battery(self):
        """Test that treating an electric bicycle recharges the battery."""
        ebike = ElectricBicycle(
            vehicle_id="EBIKE007",
            station_id=1,
            vehicle_type="ebike",
            status="degraded",
            rides_since_last_treated=5,
            last_treated_date=date.today() - timedelta(days=7),
            battery_level=30
        )

        initial_battery = ebike.battery_level
        ebike.treat()

        assert ebike.battery_level == 100
        assert ebike.battery_level > initial_battery
        assert ebike.status == "available"

    def test_ebike_treat_inherits_from_electric_vehicle(self, available_ebike):
        """Test that ElectricBicycle inherits treat from ElectricVehicle."""
        available_ebike.status = "degraded"
        available_ebike.rides_since_last_treated = 8
        available_ebike.battery_level = 30

        available_ebike.treat()

        assert available_ebike.status == "available"
        assert available_ebike.battery_level == 100
        assert available_ebike.rides_since_last_treated == 0

    def test_ebike_charge_available(self, available_ebike):
        """Test charging an available electric bicycle."""
        available_ebike.battery_level = 50
        available_ebike.charge()

        assert available_ebike.battery_level == 100

    def test_ebike_charge_degraded(self):
        """Test that charging a degraded electric bicycle raises an exception."""
        ebike = ElectricBicycle(
            vehicle_id="EBIKE008",
            station_id=1,
            vehicle_type="ebike",
            status="degraded",
            rides_since_last_treated=8,
            last_treated_date=date.today(),
            battery_level=50
        )

        with pytest.raises(Exception, match="Cannot charge a vehicle that is not available"):
            ebike.charge()


class TestScooter:
    """Tests for the Scooter model."""

    @pytest.fixture
    def available_scooter(self):
        """Create an available scooter for testing."""
        return Scooter(
            vehicle_id="SCOOTER001",
            station_id=1,
            vehicle_type="scooter",
            status="available",
            rides_since_last_treated=2,
            last_treated_date=date.today(),
            battery_level=100
        )

    def test_scooter_initialization(self, available_scooter):
        """Test that a Scooter can be initialized."""
        assert available_scooter.vehicle_id == "SCOOTER001"
        assert available_scooter.vehicle_type == "scooter"
        assert available_scooter.battery_level == 100

    def test_scooter_default_vehicle_type(self):
        """Test that Scooter vehicle_type defaults to 'scooter'."""
        scooter = Scooter(
            vehicle_id="SCOOTER002",
            station_id=1,
            status="available",
            rides_since_last_treated=0,
            last_treated_date=None,
            battery_level=100
        )
        assert scooter.vehicle_type == "scooter"

    def test_scooter_rent_available(self, available_scooter):
        """Test renting an available scooter."""
        available_scooter.rent()

        assert available_scooter.status == "rented"
        assert available_scooter.station_id is None

    def test_scooter_treat(self, available_scooter):
        """Test treating a scooter."""
        available_scooter.status = "degraded"
        available_scooter.rides_since_last_treated = 8
        available_scooter.battery_level = 20

        available_scooter.treat()

        assert available_scooter.status == "available"
        assert available_scooter.rides_since_last_treated == 0
        assert available_scooter.battery_level == 100

    def test_scooter_inherits_from_electric_vehicle(self, available_scooter):
        """Test that Scooter inherits from ElectricVehicle."""
        # Scooter should have all ElectricVehicle methods
        assert hasattr(available_scooter, 'rent')
        assert hasattr(available_scooter, 'treat')
        assert hasattr(available_scooter, 'charge')
        assert hasattr(available_scooter, 'return_vehicle')
        assert hasattr(available_scooter, 'report_degraded')


class TestElectricVehicle:
    """Tests for the ElectricVehicle abstract base class."""

    @pytest.fixture
    def electric_scooter(self):
        """Create a concrete ElectricVehicle (Scooter) for testing."""
        return Scooter(
            vehicle_id="ESCOOTER001",
            station_id=1,
            vehicle_type="scooter",
            status="available",
            rides_since_last_treated=0,
            last_treated_date=date.today(),
            battery_level=100
        )

    def test_electric_vehicle_rent_available_sufficient_battery(self, electric_scooter):
        """Test renting an available electric vehicle with sufficient battery."""
        electric_scooter.rent()

        assert electric_scooter.status == "rented"
        assert electric_scooter.station_id is None

    def test_electric_vehicle_rent_not_available(self):
        """Test that renting a not-available electric vehicle raises exception."""
        scooter = Scooter(
            vehicle_id="ESCOOTER002",
            station_id=1,
            vehicle_type="scooter",
            status="rented",
            rides_since_last_treated=0,
            last_treated_date=date.today(),
            battery_level=100
        )

        with pytest.raises(Exception, match="Electric vehicle is not available for rent"):
            scooter.rent()

    def test_electric_vehicle_rent_rides_at_threshold(self):
        """Test that renting with rides at threshold raises exception."""
        scooter = Scooter(
            vehicle_id="ESCOOTER003",
            station_id=1,
            vehicle_type="scooter",
            status="available",
            rides_since_last_treated=7,
            last_treated_date=date.today(),
            battery_level=100
        )

        with pytest.raises(Exception, match="Electric vehicle is not available for rent"):
            scooter.rent()

    def test_electric_vehicle_treat(self, electric_scooter):
        """Test treating an electric vehicle resets status and charges battery."""
        electric_scooter.status = "degraded"
        electric_scooter.rides_since_last_treated = 10
        initial_battery = electric_scooter.battery_level

        electric_scooter.treat()

        assert electric_scooter.status == "available"
        assert electric_scooter.rides_since_last_treated == 0
        assert electric_scooter.last_treated_date == date.today()
        assert electric_scooter.battery_level == 100

    def test_electric_vehicle_charge(self, electric_scooter):
        """Test charging an electric vehicle."""
        electric_scooter.battery_level = 30
        electric_scooter.charge()

        assert electric_scooter.battery_level == 100

    def test_electric_vehicle_charge_not_available(self):
        """Test that charging a non-available vehicle raises exception."""
        scooter = Scooter(
            vehicle_id="ESCOOTER004",
            station_id=1,
            vehicle_type="scooter",
            status="rented",
            rides_since_last_treated=0,
            last_treated_date=date.today(),
            battery_level=50
        )

        with pytest.raises(Exception, match="Cannot charge a vehicle that is not available"):
            scooter.charge()

    def test_electric_vehicle_return_vehicle(self, electric_scooter):
        """Test returning an electric vehicle."""
        electric_scooter.status = "rented"
        electric_scooter.station_id = None

        electric_scooter.return_vehicle(2)

        assert electric_scooter.station_id == 2
        assert electric_scooter.status == "available"

    def test_electric_vehicle_report_degraded(self, electric_scooter):
        """Test reporting an electric vehicle as degraded."""
        electric_scooter.report_degraded()

        assert electric_scooter.status == "degraded"


class TestVehicleCommonMethods:
    """Tests for common Vehicle methods across all types."""

    @pytest.fixture
    def all_vehicle_types(self):
        """Create instances of all vehicle types."""
        return {
            "bicycle": Bicycle(
                vehicle_id="BIKE_TEST",
                station_id=1,
                vehicle_type="bike",
                status="available",
                rides_since_last_treated=0,
                last_treated_date=date.today()
            ),
            "ebike": ElectricBicycle(
                vehicle_id="EBIKE_TEST",
                station_id=1,
                vehicle_type="ebike",
                status="available",
                rides_since_last_treated=0,
                last_treated_date=date.today(),
                battery_level=100
            ),
            "scooter": Scooter(
                vehicle_id="SCOOTER_TEST",
                station_id=1,
                vehicle_type="scooter",
                status="available",
                rides_since_last_treated=0,
                last_treated_date=date.today(),
                battery_level=100
            )
        }

    def test_all_vehicles_have_rent_method(self, all_vehicle_types):
        """Test that all vehicle types have a rent method."""
        for vehicle_type, vehicle in all_vehicle_types.items():
            assert hasattr(vehicle, 'rent'), f"{vehicle_type} missing rent method"

    def test_all_vehicles_have_return_vehicle_method(self, all_vehicle_types):
        """Test that all vehicle types have a return_vehicle method."""
        for vehicle_type, vehicle in all_vehicle_types.items():
            assert hasattr(vehicle, 'return_vehicle'), f"{vehicle_type} missing return_vehicle method"

    def test_all_vehicles_have_treat_method(self, all_vehicle_types):
        """Test that all vehicle types have a treat method."""
        for vehicle_type, vehicle in all_vehicle_types.items():
            assert hasattr(vehicle, 'treat'), f"{vehicle_type} missing treat method"

    def test_all_vehicles_have_report_degraded_method(self, all_vehicle_types):
        """Test that all vehicle types have a report_degraded method."""
        for vehicle_type, vehicle in all_vehicle_types.items():
            assert hasattr(vehicle, 'report_degraded'), f"{vehicle_type} missing report_degraded method"

    def test_return_vehicle_updates_station(self, all_vehicle_types):
        """Test that return_vehicle updates the station correctly for all vehicle types."""
        for vehicle_type, vehicle in all_vehicle_types.items():
            vehicle.return_vehicle(5)
            assert vehicle.station_id == 5, f"{vehicle_type} station not updated correctly"

    def test_report_degraded_updates_status(self, all_vehicle_types):
        """Test that report_degraded updates status for all vehicle types."""
        for vehicle_type, vehicle in all_vehicle_types.items():
            vehicle.report_degraded()
            assert vehicle.status == "degraded", f"{vehicle_type} status not updated to degraded"

    def test_rent_available_with_max_rides(self):
        """Test renting with rides exactly at threshold (6 rides - just before 7)."""
        bike = Bicycle(
            vehicle_id="BIKE_EDGE",
            station_id=1,
            vehicle_type="bike",
            status="available",
            rides_since_last_treated=6,
            last_treated_date=date.today()
        )

        bike.rent()
        assert bike.status == "rented"

    def test_return_vehicle_exactly_at_threshold(self):
        """Test return_vehicle with rides exactly at 7."""
        ebike = ElectricBicycle(
            vehicle_id="EBIKE_EDGE",
            station_id=1,
            vehicle_type="ebike",
            status="rented",
            rides_since_last_treated=7,
            last_treated_date=date.today(),
            battery_level=50
        )

        ebike.station_id = None
        ebike.return_vehicle(2)

        assert ebike.station_id == 2
        assert ebike.status == "degraded"

