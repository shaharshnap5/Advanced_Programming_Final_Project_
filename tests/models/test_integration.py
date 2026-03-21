# flake8: noqa
"""
Integration tests for the complete model ecosystem.
Tests that verify all models work together correctly.
"""

import pytest
from datetime import date, datetime
from src.models.station import Station, StationWithDistance
from src.models.user import User
from src.models.ride import Ride, process_end_of_ride
from src.models.vehicle import (
    Bicycle,
    ElectricBicycle,
    Scooter,
    VehicleType,
    VehicleStatus,
)


class TestCompleteFleetIntegration:
    """Integration tests for the complete fleet management system."""

    @pytest.fixture
    def fleet_system(self):
        """Create a complete fleet system with all components."""
        # Create stations
        station1 = Station(
            station_id=1,
            name="Central Station",
            lat=32.0,
            lon=34.0,
            max_capacity=20,
            vehicles=["BICYCLE001", "ELECTRIC_BICYCLE001", "SCOOTER001"],
        )
        station2 = Station(
            station_id=2,
            name="South Station",
            lat=32.1,
            lon=34.1,
            max_capacity=15,
            vehicles=["BICYCLE002"],
        )

        # Create station dictionary
        stations = {1: station1, 2: station2}

        # Create users
        user1 = User(
            user_id="USER001",
            first_name="User",
            last_name="One",
            email="user001@example.com",
            payment_token="tok_visa_001",
        )
        user2 = User(
            user_id="USER002",
            first_name="User",
            last_name="Two",
            email="user002@example.com",
            payment_token="tok_visa_002",
        )

        # Create user dictionary
        users = {"USER001": user1, "USER002": user2}

        # Create vehicles with proper enums
        bicycle = Bicycle(
            vehicle_id="BICYCLE001",
            station_id=1,
            vehicle_type=VehicleType.bicycle,
            status=VehicleStatus.available,
            rides_since_last_treated=3,
            last_treated_date=date.today(),
        )
        electric_bicycle = ElectricBicycle(
            vehicle_id="ELECTRIC_BICYCLE001",
            station_id=1,
            vehicle_type=VehicleType.electric_bicycle,
            status=VehicleStatus.available,
            rides_since_last_treated=2,
            last_treated_date=date.today(),
            battery_level=100,
        )
        scooter = Scooter(
            vehicle_id="SCOOTER001",
            station_id=1,
            vehicle_type=VehicleType.scooter,
            status=VehicleStatus.available,
            rides_since_last_treated=4,
            last_treated_date=date.today(),
            battery_level=80,
        )

        # Create active rides dictionary
        active_rides = {}

        yield {
            "stations": stations,
            "users": users,
            "active_rides": active_rides,
            "station1": station1,
            "station2": station2,
            "user1": user1,
            "user2": user2,
            "bicycle": bicycle,
            "electric_bicycle": electric_bicycle,
            "scooter": scooter,
        }

    def test_complete_ride_lifecycle(self, fleet_system):
        """Test a complete ride lifecycle: user -> vehicle -> station -> charge."""
        stations = fleet_system["stations"]
        users = fleet_system["users"]
        active_rides = fleet_system["active_rides"]
        user = fleet_system["user1"]
        bicycle = fleet_system["bicycle"]
        station1 = fleet_system["station1"]
        station2 = fleet_system["station2"]

        # Verify user can start ride (stateless)
        assert user.can_start_ride() is True

        # Rent the bicycle
        bicycle.rent()
        assert bicycle.status == VehicleStatus.rented
        assert bicycle.station_id is None

        # Remove bicycle from station
        station1.remove_vehicle("BICYCLE001")
        assert "BICYCLE001" not in station1.vehicles

        # Create and process ride
        ride = Ride(
            ride_id="RIDE001",
            user_id="USER001",
            vehicle_id="BICYCLE001",
            start_station_id=1,
            start_time=datetime.now(),
            is_degraded_report=False,
        )

        # Return vehicle to different station
        bicycle.return_vehicle(2)
        assert bicycle.station_id == 2
        assert bicycle.status == VehicleStatus.available  # Below threshold

        # Add vehicle to new station
        station2.add_vehicle("BICYCLE001")
        assert "BICYCLE001" in station2.vehicles

        # Process end of ride and charge user
        process_end_of_ride(user, ride)

    def test_multiple_users_multiple_vehicles(self, fleet_system):
        """Test multiple users renting different vehicles simultaneously."""
        stations = fleet_system["stations"]
        users = fleet_system["users"]
        active_rides = fleet_system["active_rides"]
        user1 = fleet_system["user1"]
        user2 = fleet_system["user2"]
        bicycle = fleet_system["bicycle"]
        electric_bicycle = fleet_system["electric_bicycle"]
        scooter = fleet_system["scooter"]
        station1 = fleet_system["station1"]

        # User 1 rents bicycle
        bicycle.rent()
        station1.remove_vehicle("BICYCLE001")
        assert bicycle.status == VehicleStatus.rented

        # User 2 rents electric_bicycle
        electric_bicycle.rent()
        station1.remove_vehicle("ELECTRIC_BICYCLE001")
        assert electric_bicycle.status == VehicleStatus.rented

        # Both vehicles are rented
        assert bicycle.status == VehicleStatus.rented
        assert electric_bicycle.status == VehicleStatus.rented
        assert scooter.status == VehicleStatus.available

        # Verify station has correct count
        assert len(station1.vehicles) == 1  # Only scooter left

    def test_vehicle_degradation_and_treatment(self, fleet_system):
        """Test vehicle degradation tracking and treatment."""
        stations = fleet_system["stations"]
        users = fleet_system["users"]
        active_rides = fleet_system["active_rides"]
        station1 = fleet_system["station1"]
        bicycle = fleet_system["bicycle"]
        electric_bicycle = fleet_system["electric_bicycle"]

        # bicycle has 3 rides, artificially bump to above degradation threshold (>10)
        bicycle.rides_since_last_treated = 11
        bicycle.return_vehicle(1)
        assert bicycle.status == VehicleStatus.degraded

        # Treat the bicycle
        bicycle.treat()
        assert bicycle.status == VehicleStatus.available
        assert bicycle.rides_since_last_treated == 0
        assert bicycle.last_treated_date == date.today()

        # E-bicycle treatment with battery
        electric_bicycle.status = VehicleStatus.degraded
        electric_bicycle.rides_since_last_treated = 8
        electric_bicycle.battery_level = 25

        electric_bicycle.treat()
        assert electric_bicycle.status == VehicleStatus.available
        assert electric_bicycle.rides_since_last_treated == 0
        assert electric_bicycle.battery_level == 100

    def test_station_capacity_management(self, fleet_system):
        """Test station capacity constraints."""
        stations = fleet_system["stations"]
        users = fleet_system["users"]
        active_rides = fleet_system["active_rides"]
        station2 = fleet_system["station2"]

        # Station 2 has capacity 15, currently has 1 vehicle
        assert station2.has_free_spot() is True
        assert station2.has_available_vehicle() is True

        # Add vehicles up to capacity
        for i in range(14):
            station2.add_vehicle(f"VEHICLE_{i:03d}")

        assert len(station2.vehicles) == 15  # Full now
        assert station2.has_free_spot() is False

        # Try to add when full
        with pytest.raises(Exception, match="Station is at full capacity"):
            station2.add_vehicle("OVERFLOW")

    def test_electric_vehicle_battery_constraint(self, fleet_system):
        """Test electric vehicle battery constraints on renting."""
        stations = fleet_system["stations"]
        users = fleet_system["users"]
        active_rides = fleet_system["active_rides"]
        electric_bicycle = fleet_system["electric_bicycle"]
        scooter = fleet_system["scooter"]

        # electric_bicycle with full battery should rent
        electric_bicycle.battery_level = 100
        electric_bicycle.rent()
        assert electric_bicycle.status == VehicleStatus.rented

        # Reset for next test
        electric_bicycle.status = VehicleStatus.available
        electric_bicycle.station_id = 1

        # Scooter with low battery shouldn't rent
        scooter.battery_level = 13  # Below 14% threshold
        with pytest.raises(
            Exception, match="Electric vehicle is not available for rent"
        ):
            scooter.rent()

        # After charging, should rent
        scooter.battery_level = 100
        scooter.rent()
        assert scooter.status == VehicleStatus.rented

    def test_fleet_state_management(self, fleet_system):
        """Test fleet system maintains correct state."""
        stations = fleet_system["stations"]
        users = fleet_system["users"]
        active_rides = fleet_system["active_rides"]
        user1 = fleet_system["user1"]
        station1 = fleet_system["station1"]
        bicycle = fleet_system["bicycle"]

        # Create a ride and add to active rides
        ride = Ride(ride_id="RIDE001", user_id="USER001", vehicle_id="BICYCLE001")
        active_rides["RIDE001"] = ride

        # Verify all state dictionaries
        assert len(stations) >= 2
        assert len(users) >= 2
        assert len(active_rides) >= 1

        # Verify retrieval
        retrieved_ride = active_rides.get("RIDE001")
        assert retrieved_ride is not None
        assert retrieved_ride.user_id == "USER001"

        # Process end of ride
        process_end_of_ride(user1, ride)

        # Clean up active ride
        del active_rides["RIDE001"]
        assert "RIDE001" not in active_rides

    def test_ride_cost_calculation_integration(self, fleet_system):
        """Test ride cost calculation in complete scenarios."""
        user = fleet_system["user1"]

        # Normal ride
        normal_ride = Ride(
            ride_id="RIDE_NORMAL",
            user_id="USER001",
            vehicle_id="BICYCLE001",
            start_station_id=1,
            start_time=datetime.now(),
            is_degraded_report=False,
        )
        assert normal_ride.calculate_cost() == 15

        # Degraded ride
        degraded_ride = Ride(
            ride_id="RIDE_DEGRADED",
            user_id="USER001",
            vehicle_id="BICYCLE001",
            start_station_id=1,
            start_time=datetime.now(),
            is_degraded_report=True,
        )
        assert degraded_ride.calculate_cost() == 0

        # User should be charged correctly
        process_end_of_ride(user, normal_ride)

        process_end_of_ride(user, degraded_ride)

    def test_station_with_distance_functionality(self, fleet_system):
        """Test StationWithDistance for nearest station queries."""
        station1 = fleet_system["station1"]

        # Create stations with distances
        nearby_station = StationWithDistance(
            station_id=1,
            name="Central Station",
            lat=32.0,
            lon=34.0,
            max_capacity=20,
            vehicles=["BICYCLE001"],
            distance=0.5,
        )
        far_station = StationWithDistance(
            station_id=2,
            name="Far Station",
            lat=32.5,
            lon=34.5,
            max_capacity=15,
            vehicles=["BICYCLE002"],
            distance=5.0,
        )

        # Verify distance comparison
        assert nearby_station.distance < far_station.distance

        # Both should have functionality
        assert nearby_station.has_available_vehicle() is True
        assert far_station.has_available_vehicle() is True

        # Can add/remove vehicles
        nearby_station.add_vehicle("BICYCLE003")
        assert len(nearby_station.vehicles) == 2

        nearby_station.remove_vehicle("BICYCLE001")
        assert len(nearby_station.vehicles) == 1

    def test_complete_system_workflow(self, fleet_system):
        """Test a complete workflow through the system."""
        stations = fleet_system["stations"]
        users = fleet_system["users"]
        active_rides = fleet_system["active_rides"]
        user = fleet_system["user1"]
        station1 = fleet_system["station1"]
        station2 = fleet_system["station2"]
        bicycle = fleet_system["bicycle"]

        # 1. User registers (already done in fixture)
        assert user.user_id in users
        assert user.can_start_ride() is True

        # 2. Find nearest station (simplified - just check stations exist)
        assert 1 in stations
        assert 2 in stations

        # 3. Select vehicle and start ride
        assert user.can_start_ride() is True

        bicycle.rent()
        assert bicycle.status == VehicleStatus.rented
        station1.remove_vehicle("BICYCLE001")

        # 4. Ride in progress
        assert bicycle.status == VehicleStatus.rented

        # 5. End ride at different station
        bicycle.return_vehicle(2)
        station2.add_vehicle("BICYCLE001")

        # 6. Process payment
        ride = Ride(
            ride_id="TRIP001",
            user_id="USER001",
            vehicle_id="BICYCLE001",
            is_degraded_report=False,
        )
        process_end_of_ride(user, ride)

        # 7. Verify final state
        assert bicycle.status == VehicleStatus.available
        assert bicycle.station_id == 2
        assert "BICYCLE001" in station2.vehicles
        assert "BICYCLE001" not in station1.vehicles


class TestErrorHandlingIntegration:
    """Integration tests for error handling across models."""

    def test_invalid_operations_are_caught(self):
        """Test that invalid operations raise appropriate errors."""
        bicycle = Bicycle(
            vehicle_id="bicycle_ERR",
            station_id=1,
            vehicle_type=VehicleType.bicycle,
            status=VehicleStatus.degraded,
            rides_since_last_treated=0,
            last_treated_date=date.today(),
        )

        # Can't rent degraded vehicle
        with pytest.raises(Exception):
            bicycle.rent()

        # Station overflow
        station = Station(
            station_id=99,
            name="Small Station",
            lat=32.0,
            lon=34.0,
            max_capacity=1,
            vehicles=["V001"],
        )

        with pytest.raises(Exception):
            station.add_vehicle("V002")

        # Invalid user charging
        user = User(
            user_id="INVALID",
            first_name="Invalid",
            last_name="User",
            email="invalid.user@example.com",
            payment_token="",
        )
        with pytest.raises(ValueError):
            user.charge(15)

    def test_state_consistency_across_operations(self):
        """Test that state remains consistent across multiple operations."""
        user = User(
            user_id="CONSISTENCY_TEST",
            first_name="Consistency",
            last_name="User",
            email="consistency.user@example.com",
            payment_token="tok_123",
        )
        station = Station(
            station_id=1,
            name="Consistency Station",
            lat=32.0,
            lon=34.0,
            max_capacity=5,
            vehicles=[],
        )

        # Add vehicles
        for i in range(3):
            station.add_vehicle(f"V{i}")

        assert len(station.vehicles) == 3
        assert station.has_available_vehicle() is True
        assert station.has_free_spot() is True

        # Remove and re-add
        station.remove_vehicle("V0")
        assert len(station.vehicles) == 2

        station.add_vehicle("V0")
        assert len(station.vehicles) == 3

        # User remains stateless regarding active rides
        assert user.can_start_ride() is True


class TestCompleteFleetIntegration:
    """Integration tests for the complete fleet management system."""

    @pytest.fixture
    def fleet_system(self):
        """Create a complete fleet system with all components."""
        # Create stations
        station1 = Station(
            station_id=1,
            name="Central Station",
            lat=32.0,
            lon=34.0,
            max_capacity=20,
            vehicles=["BICYCLE001", "ELECTRIC_BICYCLE001", "SCOOTER001"],
        )
        station2 = Station(
            station_id=2,
            name="South Station",
            lat=32.1,
            lon=34.1,
            max_capacity=15,
            vehicles=["BICYCLE002"],
        )

        # Create station dictionary
        stations = {1: station1, 2: station2}

        # Create users
        user1 = User(
            user_id="USER001",
            first_name="User",
            last_name="One",
            email="user001@example.com",
            payment_token="tok_visa_001",
        )
        user2 = User(
            user_id="USER002",
            first_name="User",
            last_name="Two",
            email="user002@example.com",
            payment_token="tok_visa_002",
        )

        # Create user dictionary
        users = {"USER001": user1, "USER002": user2}

        # Create vehicles
        bicycle = Bicycle(
            vehicle_id="BICYCLE001",
            station_id=1,
            vehicle_type=VehicleType.bicycle,
            status=VehicleStatus.available,
            rides_since_last_treated=3,
            last_treated_date=date.today(),
        )
        electric_bicycle = ElectricBicycle(
            vehicle_id="ELECTRIC_BICYCLE001",
            station_id=1,
            vehicle_type=VehicleType.electric_bicycle,
            status=VehicleStatus.available,
            rides_since_last_treated=2,
            last_treated_date=date.today(),
            battery_level=100,
        )
        scooter = Scooter(
            vehicle_id="SCOOTER001",
            station_id=1,
            vehicle_type=VehicleType.scooter,
            status=VehicleStatus.available,
            rides_since_last_treated=4,
            last_treated_date=date.today(),
            battery_level=80,
        )

        # Create active rides dictionary
        active_rides = {}

        yield {
            "stations": stations,
            "users": users,
            "active_rides": active_rides,
            "station1": station1,
            "station2": station2,
            "user1": user1,
            "user2": user2,
            "bicycle": bicycle,
            "electric_bicycle": electric_bicycle,
            "scooter": scooter,
        }

    def test_complete_ride_lifecycle(self, fleet_system):
        """Test a complete ride lifecycle: user -> vehicle -> station -> charge."""
        stations = fleet_system["stations"]
        users = fleet_system["users"]
        active_rides = fleet_system["active_rides"]
        user = fleet_system["user1"]
        bicycle = fleet_system["bicycle"]
        station1 = fleet_system["station1"]
        station2 = fleet_system["station2"]

        # Verify user can start ride (stateless)
        assert user.can_start_ride() is True

        # Rent the bicycle
        bicycle.rent()
        assert bicycle.status == "rented"
        assert bicycle.station_id is None

        # Remove bicycle from station
        station1.remove_vehicle("BICYCLE001")
        assert "BICYCLE001" not in station1.vehicles

        # Create and process ride
        ride = Ride(
            ride_id="RIDE001",
            user_id="USER001",
            vehicle_id="BICYCLE001",
            start_station_id=1,
            start_time=datetime.now(),
            is_degraded_report=False,
        )

        # Return vehicle to different station
        bicycle.return_vehicle(2)
        assert bicycle.station_id == 2
        assert bicycle.status == "available"  # Below threshold

        # Add vehicle to new station
        station2.add_vehicle("BICYCLE001")
        assert "BICYCLE001" in station2.vehicles

        # Process end of ride and charge user
        process_end_of_ride(user, ride)

    def test_multiple_users_multiple_vehicles(self, fleet_system):
        """Test multiple users renting different vehicles simultaneously."""
        stations = fleet_system["stations"]
        users = fleet_system["users"]
        active_rides = fleet_system["active_rides"]
        user1 = fleet_system["user1"]
        user2 = fleet_system["user2"]
        bicycle = fleet_system["bicycle"]
        electric_bicycle = fleet_system["electric_bicycle"]
        scooter = fleet_system["scooter"]
        station1 = fleet_system["station1"]

        # User 1 rents bicycle
        bicycle.rent()
        station1.remove_vehicle("BICYCLE001")
        assert bicycle.status == "rented"

        # User 2 rents electric_bicycle
        electric_bicycle.rent()
        station1.remove_vehicle("ELECTRIC_BICYCLE001")
        assert electric_bicycle.status == "rented"

        # Both vehicles are rented
        assert bicycle.status == "rented"
        assert electric_bicycle.status == "rented"
        assert scooter.status == "available"

        # Verify station has correct count
        assert len(station1.vehicles) == 1  # Only scooter left

    def test_vehicle_degradation_and_treatment(self, fleet_system):
        """Test vehicle degradation tracking and treatment."""
        stations = fleet_system["stations"]
        users = fleet_system["users"]
        active_rides = fleet_system["active_rides"]
        station1 = fleet_system["station1"]
        bicycle = fleet_system["bicycle"]
        electric_bicycle = fleet_system["electric_bicycle"]

        # bicycle has 3 rides, artificially bump to above degradation threshold (>10)
        bicycle.rides_since_last_treated = 11
        bicycle.return_vehicle(1)
        assert bicycle.status == "degraded"

        # Treat the bicycle
        bicycle.treat()
        assert bicycle.status == "available"
        assert bicycle.rides_since_last_treated == 0
        assert bicycle.last_treated_date == date.today()

        # E-bicycle treatment with battery
        electric_bicycle.status = "degraded"
        electric_bicycle.rides_since_last_treated = 8
        electric_bicycle.battery_level = 25

        electric_bicycle.treat()
        assert electric_bicycle.status == "available"
        assert electric_bicycle.rides_since_last_treated == 0
        assert electric_bicycle.battery_level == 100

    def test_station_capacity_management(self, fleet_system):
        """Test station capacity constraints."""
        stations = fleet_system["stations"]
        users = fleet_system["users"]
        active_rides = fleet_system["active_rides"]
        station2 = fleet_system["station2"]

        # Station 2 has capacity 15, currently has 1 vehicle
        assert station2.has_free_spot() is True
        assert station2.has_available_vehicle() is True

        # Add vehicles up to capacity
        for i in range(14):
            station2.add_vehicle(f"VEHICLE_{i:03d}")

        assert len(station2.vehicles) == 15  # Full now
        assert station2.has_free_spot() is False

        # Try to add when full
        with pytest.raises(Exception, match="Station is at full capacity"):
            station2.add_vehicle("OVERFLOW")

    def test_electric_vehicle_battery_constraint(self, fleet_system):
        """Test electric vehicle battery constraints on renting."""
        stations = fleet_system["stations"]
        users = fleet_system["users"]
        active_rides = fleet_system["active_rides"]
        electric_bicycle = fleet_system["electric_bicycle"]
        scooter = fleet_system["scooter"]

        # electric_bicycle with full battery should rent
        electric_bicycle.battery_level = 100
        electric_bicycle.rent()
        assert electric_bicycle.status == "rented"

        # Reset for next test
        electric_bicycle.status = "available"
        electric_bicycle.station_id = 1

        # Scooter with low battery shouldn't rent
        scooter.battery_level = 13  # Below 14% threshold
        with pytest.raises(
            Exception, match="Electric vehicle is not available for rent"
        ):
            scooter.rent()

        # After charging, should rent
        scooter.battery_level = 100
        scooter.rent()
        assert scooter.status == "rented"

    def test_fleet_state_management(self, fleet_system):
        """Test fleet system maintains correct state."""
        stations = fleet_system["stations"]
        users = fleet_system["users"]
        active_rides = fleet_system["active_rides"]
        user1 = fleet_system["user1"]
        station1 = fleet_system["station1"]
        bicycle = fleet_system["bicycle"]

        # Create a ride and add to active rides
        ride = Ride(
            ride_id="RIDE001",
            user_id="USER001",
            vehicle_id="BICYCLE001",
            start_station_id=1,
            start_time=datetime.now(),
        )
        active_rides["RIDE001"] = ride

        # Verify all state dictionaries
        assert len(stations) >= 2
        assert len(users) >= 2
        assert len(active_rides) >= 1

        # Verify retrieval
        retrieved_ride = active_rides.get("RIDE001")
        assert retrieved_ride is not None
        assert retrieved_ride.user_id == "USER001"

        # Process end of ride
        process_end_of_ride(user1, ride)

        # Clean up active ride
        del active_rides["RIDE001"]
        assert "RIDE001" not in active_rides

    def test_ride_cost_calculation_integration(self, fleet_system):
        """Test ride cost calculation in complete scenarios."""
        user = fleet_system["user1"]

        # Normal ride
        normal_ride = Ride(
            ride_id="RIDE_NORMAL",
            user_id="USER001",
            vehicle_id="BICYCLE001",
            start_station_id=1,
            start_time=datetime.now(),
            is_degraded_report=False,
        )
        assert normal_ride.calculate_cost() == 15

        # Degraded ride
        degraded_ride = Ride(
            ride_id="RIDE_DEGRADED",
            user_id="USER001",
            vehicle_id="BICYCLE001",
            start_station_id=1,
            start_time=datetime.now(),
            is_degraded_report=True,
        )
        assert degraded_ride.calculate_cost() == 0

        # User should be charged correctly
        process_end_of_ride(user, normal_ride)

        process_end_of_ride(user, degraded_ride)

    def test_station_with_distance_functionality(self, fleet_system):
        """Test StationWithDistance for nearest station queries."""
        station1 = fleet_system["station1"]

        # Create stations with distances
        nearby_station = StationWithDistance(
            station_id=1,
            name="Central Station",
            lat=32.0,
            lon=34.0,
            max_capacity=20,
            vehicles=["BICYCLE001"],
            distance=0.5,
        )
        far_station = StationWithDistance(
            station_id=2,
            name="Far Station",
            lat=32.5,
            lon=34.5,
            max_capacity=15,
            vehicles=["BICYCLE002"],
            distance=5.0,
        )

        # Verify distance comparison
        assert nearby_station.distance < far_station.distance

        # Both should have functionality
        assert nearby_station.has_available_vehicle() is True
        assert far_station.has_available_vehicle() is True

        # Can add/remove vehicles
        nearby_station.add_vehicle("BICYCLE003")
        assert len(nearby_station.vehicles) == 2

        nearby_station.remove_vehicle("BICYCLE001")
        assert len(nearby_station.vehicles) == 1

    def test_complete_system_workflow(self, fleet_system):
        """Test a complete workflow through the system."""
        stations = fleet_system["stations"]
        users = fleet_system["users"]
        active_rides = fleet_system["active_rides"]
        user = fleet_system["user1"]
        station1 = fleet_system["station1"]
        station2 = fleet_system["station2"]
        bicycle = fleet_system["bicycle"]

        # 1. User registers (already done in fixture)
        assert user.user_id in users
        assert user.can_start_ride() is True

        # 2. Find nearest station (simplified - just check stations exist)
        assert 1 in stations
        assert 2 in stations

        # 3. Select vehicle and start ride
        assert user.can_start_ride() is True

        bicycle.rent()
        assert bicycle.status == "rented"
        station1.remove_vehicle("BICYCLE001")

        # 4. Ride in progress
        assert bicycle.status == "rented"

        # 5. End ride at different station
        bicycle.return_vehicle(2)
        station2.add_vehicle("BICYCLE001")

        # 6. Process payment
        ride = Ride(
            ride_id="TRIP001",
            user_id="USER001",
            vehicle_id="BICYCLE001",
            start_station_id=1,
            start_time=datetime.now(),
            is_degraded_report=False,
        )
        process_end_of_ride(user, ride)

        # 7. Verify final state
        assert bicycle.status == "available"
        assert bicycle.station_id == 2
        assert "BICYCLE001" in station2.vehicles
        assert "BICYCLE001" not in station1.vehicles


class TestErrorHandlingIntegration:
    """Integration tests for error handling across models."""

    def test_invalid_operations_are_caught(self):
        """Test that invalid operations raise appropriate errors."""
        bicycle = Bicycle(
            vehicle_id="bicycle_ERR",
            station_id=1,
            vehicle_type=VehicleType.bicycle,
            status=VehicleStatus.degraded,
            rides_since_last_treated=0,
            last_treated_date=date.today(),
        )

        # Can't rent degraded vehicle
        with pytest.raises(Exception):
            bicycle.rent()

        # Station overflow
        station = Station(
            station_id=99,
            name="Small Station",
            lat=32.0,
            lon=34.0,
            max_capacity=1,
            vehicles=["V001"],
        )

        with pytest.raises(Exception):
            station.add_vehicle("V002")

        # Invalid user charging
        user = User(
            user_id="INVALID",
            first_name="Invalid",
            last_name="User",
            email="invalid.user@example.com",
            payment_token="",
        )
        with pytest.raises(ValueError):
            user.charge(15)

    def test_state_consistency_across_operations(self):
        """Test that state remains consistent across multiple operations."""
        user = User(
            user_id="CONSISTENCY_TEST",
            first_name="Consistency",
            last_name="User",
            email="consistency.user@example.com",
            payment_token="tok_123",
        )
        station = Station(
            station_id=1,
            name="Consistency Station",
            lat=32.0,
            lon=34.0,
            max_capacity=5,
            vehicles=[],
        )

        # Add vehicles
        for i in range(3):
            station.add_vehicle(f"V{i}")

        assert len(station.vehicles) == 3
        assert station.has_available_vehicle() is True
        assert station.has_free_spot() is True

        # Remove and re-add
        station.remove_vehicle("V0")
        assert len(station.vehicles) == 2

        station.add_vehicle("V0")
        assert len(station.vehicles) == 3

        # User remains stateless regarding active rides
        assert user.can_start_ride() is True
