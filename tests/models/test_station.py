"""
Comprehensive tests for the Station models with 100% coverage.
Tests cover:
- Station initialization and validation
- has_available_vehicle method
- has_free_spot method
- add_vehicle method
- remove_vehicle method
- StationWithDistance model
"""

import pytest
from unittest.mock import Mock

from src.models.station import Station, StationWithDistance


class TestStation:
    """Tests for the Station model."""

    @pytest.fixture
    def empty_station(self):
        """Create an empty station with no vehicles."""
        return Station(
            station_id=1,
            name="Empty Station",
            lat=32.0,
            lon=34.0,
            max_capacity=10,
            vehicles=[]
        )

    @pytest.fixture
    def full_station(self):
        """Create a station at full capacity."""
        vehicles = [f"VEHICLE_{i:03d}" for i in range(10)]
        return Station(
            station_id=2,
            name="Full Station",
            lat=32.1,
            lon=34.1,
            max_capacity=10,
            vehicles=vehicles
        )

    @pytest.fixture
    def partial_station(self):
        """Create a station with some vehicles."""
        return Station(
            station_id=3,
            name="Partial Station",
            lat=32.2,
            lon=34.2,
            max_capacity=20,
            vehicles=["VEHICLE_001", "VEHICLE_002", "VEHICLE_003"]
        )

    def test_station_initialization(self, empty_station):
        """Test that a Station can be initialized with required fields."""
        assert empty_station.station_id == 1
        assert empty_station.name == "Empty Station"
        assert empty_station.lat == 32.0
        assert empty_station.lon == 34.0
        assert empty_station.max_capacity == 10
        assert empty_station.vehicles == []

    def test_station_initialization_with_vehicles(self, partial_station):
        """Test that a Station can be initialized with vehicles."""
        assert len(partial_station.vehicles) == 3
        assert "VEHICLE_001" in partial_station.vehicles

    def test_station_default_vehicles_empty_list(self):
        """Test that vehicles defaults to an empty list."""
        station = Station(
            station_id=4,
            name="Test Station",
            lat=32.3,
            lon=34.3,
            max_capacity=5
        )
        assert station.vehicles == []
        assert isinstance(station.vehicles, list)

    def test_has_available_vehicle_with_vehicles(self, partial_station):
        """Test has_available_vehicle returns True when vehicles are present."""
        assert partial_station.has_available_vehicle() is True

    def test_has_available_vehicle_empty_station(self, empty_station):
        """Test has_available_vehicle returns False for empty station."""
        assert empty_station.has_available_vehicle() is False

    def test_has_available_vehicle_single_vehicle(self):
        """Test has_available_vehicle with exactly one vehicle."""
        station = Station(
            station_id=5,
            name="Single Vehicle Station",
            lat=32.4,
            lon=34.4,
            max_capacity=5,
            vehicles=["VEHICLE_001"]
        )
        assert station.has_available_vehicle() is True

    def test_has_free_spot_empty_station(self, empty_station):
        """Test has_free_spot returns True for empty station."""
        assert empty_station.has_free_spot() is True

    def test_has_free_spot_with_capacity(self, partial_station):
        """Test has_free_spot returns True when capacity available."""
        assert partial_station.has_free_spot() is True

    def test_has_free_spot_full_station(self, full_station):
        """Test has_free_spot returns False for full station."""
        assert full_station.has_free_spot() is False

    def test_has_free_spot_at_capacity(self):
        """Test has_free_spot when vehicles exactly equal max_capacity."""
        station = Station(
            station_id=6,
            name="At Capacity Station",
            lat=32.5,
            lon=34.5,
            max_capacity=5,
            vehicles=["V1", "V2", "V3", "V4", "V5"]
        )
        assert station.has_free_spot() is False

    def test_add_vehicle_to_empty_station(self, empty_station):
        """Test adding a vehicle to an empty station."""
        empty_station.add_vehicle("VEHICLE_001")

        assert len(empty_station.vehicles) == 1
        assert "VEHICLE_001" in empty_station.vehicles

    def test_add_vehicle_to_partial_station(self, partial_station):
        """Test adding a vehicle to a station with capacity."""
        initial_count = len(partial_station.vehicles)
        partial_station.add_vehicle("VEHICLE_004")

        assert len(partial_station.vehicles) == initial_count + 1
        assert "VEHICLE_004" in partial_station.vehicles

    def test_add_vehicle_to_full_station(self, full_station):
        """Test that adding to a full station raises an exception."""
        with pytest.raises(Exception, match="Station is at full capacity"):
            full_station.add_vehicle("VEHICLE_010")

    def test_add_vehicle_multiple_vehicles(self, empty_station):
        """Test adding multiple vehicles sequentially."""
        for i in range(5):
            empty_station.add_vehicle(f"VEHICLE_{i:03d}")

        assert len(empty_station.vehicles) == 5
        for i in range(5):
            assert f"VEHICLE_{i:03d}" in empty_station.vehicles

    def test_add_vehicle_at_capacity_limit(self):
        """Test adding the last vehicle to reach capacity."""
        station = Station(
            station_id=7,
            name="Near Capacity",
            lat=32.6,
            lon=34.6,
            max_capacity=5,
            vehicles=["V1", "V2", "V3", "V4"]
        )

        station.add_vehicle("V5")
        assert len(station.vehicles) == 5
        assert station.has_free_spot() is False

    def test_remove_vehicle_from_station(self, partial_station):
        """Test removing a vehicle from a station."""
        initial_count = len(partial_station.vehicles)
        partial_station.remove_vehicle("VEHICLE_001")

        assert len(partial_station.vehicles) == initial_count - 1
        assert "VEHICLE_001" not in partial_station.vehicles

    def test_remove_vehicle_not_found(self, partial_station):
        """Test that removing non-existent vehicle raises exception."""
        with pytest.raises(Exception, match="Vehicle not found at this station"):
            partial_station.remove_vehicle("VEHICLE_999")

    def test_remove_vehicle_from_full_station(self, full_station):
        """Test removing a vehicle from a full station."""
        initial_count = len(full_station.vehicles)
        vehicle_to_remove = full_station.vehicles[0]

        full_station.remove_vehicle(vehicle_to_remove)

        assert len(full_station.vehicles) == initial_count - 1
        assert vehicle_to_remove not in full_station.vehicles
        assert full_station.has_free_spot() is True

    def test_remove_multiple_vehicles(self, partial_station):
        """Test removing multiple vehicles sequentially."""
        partial_station.remove_vehicle("VEHICLE_001")
        assert len(partial_station.vehicles) == 2

        partial_station.remove_vehicle("VEHICLE_002")
        assert len(partial_station.vehicles) == 1

        partial_station.remove_vehicle("VEHICLE_003")
        assert len(partial_station.vehicles) == 0

    def test_station_is_pydantic_model(self, empty_station):
        """Test that Station is a Pydantic BaseModel."""
        station_dict = empty_station.model_dump()
        assert isinstance(station_dict, dict)
        assert "station_id" in station_dict
        assert "name" in station_dict
        assert "lat" in station_dict
        assert "lon" in station_dict
        assert "max_capacity" in station_dict
        assert "vehicles" in station_dict

    def test_station_validation_missing_required_field(self):
        """Test that Station validation fails when required fields are missing."""
        with pytest.raises(Exception):  # Pydantic will raise validation error
            Station(
                station_id=8,
                name="Incomplete Station",
                lat=32.7
                # Missing lon and max_capacity
            )

    def test_add_then_remove_same_vehicle(self, empty_station):
        """Test adding and removing the same vehicle."""
        empty_station.add_vehicle("VEHICLE_TEST")
        assert len(empty_station.vehicles) == 1

        empty_station.remove_vehicle("VEHICLE_TEST")
        assert len(empty_station.vehicles) == 0

    def test_station_coordinates_precision(self):
        """Test that station coordinates can handle float precision."""
        station = Station(
            station_id=9,
            name="Precision Test",
            lat=32.123456789,
            lon=34.987654321,
            max_capacity=10
        )

        assert station.lat == 32.123456789
        assert station.lon == 34.987654321

    def test_add_duplicate_vehicle(self, partial_station):
        """Test adding a duplicate vehicle (should be allowed)."""
        initial_count = len(partial_station.vehicles)
        partial_station.add_vehicle("VEHICLE_001")  # Already exists

        # Pydantic allows duplicates in lists
        assert len(partial_station.vehicles) == initial_count + 1

    def test_add_vehicle_with_none_vehicles_list(self):
        """Test adding a vehicle when vehicles list is None (edge case)."""
        station = Station(
            station_id=10,
            name="None Vehicles Station",
            lat=32.8,
            lon=34.8,
            max_capacity=10
        )
        # Manually set to None to test the guard clause
        station.vehicles = None

        station.add_vehicle("VEHICLE_NONE")

        assert station.vehicles is not None
        assert len(station.vehicles) == 1
        assert "VEHICLE_NONE" in station.vehicles


class TestStationWithDistance:
    """Tests for the StationWithDistance model."""

    @pytest.fixture
    def station_with_distance(self):
        """Create a StationWithDistance instance."""
        return StationWithDistance(
            station_id=1,
            name="Nearby Station",
            lat=32.0,
            lon=34.0,
            max_capacity=10,
            vehicles=["VEHICLE_001", "VEHICLE_002"],
            distance=0.5
        )

    def test_station_with_distance_initialization(self, station_with_distance):
        """Test that StationWithDistance can be initialized."""
        assert station_with_distance.station_id == 1
        assert station_with_distance.name == "Nearby Station"
        assert station_with_distance.distance == 0.5

    def test_station_with_distance_inherits_from_station(self, station_with_distance):
        """Test that StationWithDistance inherits Station properties."""
        assert station_with_distance.lat == 32.0
        assert station_with_distance.lon == 34.0
        assert station_with_distance.max_capacity == 10
        assert len(station_with_distance.vehicles) == 2

    def test_station_with_distance_has_available_vehicle(self, station_with_distance):
        """Test has_available_vehicle on StationWithDistance."""
        assert station_with_distance.has_available_vehicle() is True

    def test_station_with_distance_has_free_spot(self, station_with_distance):
        """Test has_free_spot on StationWithDistance."""
        assert station_with_distance.has_free_spot() is True

    def test_station_with_distance_add_vehicle(self, station_with_distance):
        """Test adding a vehicle to StationWithDistance."""
        station_with_distance.add_vehicle("VEHICLE_003")

        assert len(station_with_distance.vehicles) == 3
        assert "VEHICLE_003" in station_with_distance.vehicles
        assert station_with_distance.distance == 0.5  # Distance unchanged

    def test_station_with_distance_remove_vehicle(self, station_with_distance):
        """Test removing a vehicle from StationWithDistance."""
        station_with_distance.remove_vehicle("VEHICLE_001")

        assert len(station_with_distance.vehicles) == 1
        assert "VEHICLE_001" not in station_with_distance.vehicles

    def test_station_with_distance_zero_distance(self):
        """Test StationWithDistance with zero distance."""
        station = StationWithDistance(
            station_id=2,
            name="Current Location",
            lat=32.1,
            lon=34.1,
            max_capacity=5,
            distance=0.0
        )

        assert station.distance == 0.0

    def test_station_with_distance_large_distance(self):
        """Test StationWithDistance with large distance."""
        station = StationWithDistance(
            station_id=3,
            name="Far Station",
            lat=32.2,
            lon=34.2,
            max_capacity=5,
            distance=50.5
        )

        assert station.distance == 50.5

    def test_station_with_distance_comparison(self):
        """Test comparing stations by distance."""
        station1 = StationWithDistance(
            station_id=4,
            name="Station 1",
            lat=32.3,
            lon=34.3,
            max_capacity=5,
            distance=1.5
        )
        station2 = StationWithDistance(
            station_id=5,
            name="Station 2",
            lat=32.4,
            lon=34.4,
            max_capacity=5,
            distance=3.0
        )

        assert station1.distance < station2.distance

    def test_station_with_distance_is_pydantic_model(self, station_with_distance):
        """Test that StationWithDistance is a Pydantic BaseModel."""
        station_dict = station_with_distance.model_dump()
        assert isinstance(station_dict, dict)
        assert "distance" in station_dict
        assert "station_id" in station_dict
        assert "name" in station_dict

