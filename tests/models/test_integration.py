"""
Integration tests for the complete model ecosystem.
Tests that verify all models work together correctly.
"""

import pytest
from datetime import date
from src.models.FleetManager import FleetManager
from src.models.station import Station, StationWithDistance
from src.models.user import User
from src.models.ride import Ride, process_end_of_ride
from src.models.vehicle import Bicycle, ElectricBicycle, Scooter


class TestCompleteFleetIntegration:
    """Integration tests for the complete fleet management system."""

    @pytest.fixture
    def fleet_system(self):
        """Create a complete fleet system with all components."""
        FleetManager._instance = None
        fm = FleetManager()

        # Create stations
        station1 = Station(
            station_id=1,
            name="Central Station",
            lat=32.0,
            lon=34.0,
            max_capacity=20,
            vehicles=["BIKE001", "EBIKE001", "SCOOTER001"]
        )
        station2 = Station(
            station_id=2,
            name="South Station",
            lat=32.1,
            lon=34.1,
            max_capacity=15,
            vehicles=["BIKE002"]
        )

        fm.stations[1] = station1
        fm.stations[2] = station2

        # Create users
        user1 = User(user_id="USER001", payment_token="tok_visa_001")
        user2 = User(user_id="USER002", payment_token="tok_visa_002")

        fm.users["USER001"] = user1
        fm.users["USER002"] = user2

        # Create vehicles
        bike = Bicycle(
            vehicle_id="BIKE001",
            station_id=1,
            vehicle_type="bike",
            status="available",
            rides_since_last_treated=3,
            last_treated_date=date.today()
        )
        ebike = ElectricBicycle(
            vehicle_id="EBIKE001",
            station_id=1,
            vehicle_type="ebike",
            status="available",
            rides_since_last_treated=2,
            last_treated_date=date.today(),
            battery_level=100
        )
        scooter = Scooter(
            vehicle_id="SCOOTER001",
            station_id=1,
            vehicle_type="scooter",
            status="available",
            rides_since_last_treated=4,
            last_treated_date=date.today(),
            battery_level=80
        )

        yield {
            'fleet_manager': fm,
            'station1': station1,
            'station2': station2,
            'user1': user1,
            'user2': user2,
            'bike': bike,
            'ebike': ebike,
            'scooter': scooter
        }

        FleetManager._instance = None

    def test_complete_ride_lifecycle(self, fleet_system):
        """Test a complete ride lifecycle: user -> vehicle -> station -> charge."""
        fm = fleet_system['fleet_manager']
        user = fleet_system['user1']
        bike = fleet_system['bike']
        station1 = fleet_system['station1']
        station2 = fleet_system['station2']

        # Verify user can start ride
        assert user.can_start_ride() is True

        # Simulate ride start
        user.current_ride_id = "RIDE001"
        assert user.can_start_ride() is False

        # Rent the bike
        bike.rent()
        assert bike.status == "rented"
        assert bike.station_id is None

        # Remove bike from station
        station1.remove_vehicle("BIKE001")
        assert "BIKE001" not in station1.vehicles

        # Create and process ride
        ride = Ride(
            ride_id="RIDE001",
            user_id="USER001",
            vehicle_id="BIKE001",
            is_degraded_report=False
        )

        # Return vehicle to different station
        bike.return_vehicle(2)
        assert bike.station_id == 2
        assert bike.status == "available"  # Below threshold

        # Add vehicle to new station
        station2.add_vehicle("BIKE001")
        assert "BIKE001" in station2.vehicles

        # Process end of ride and charge user
        process_end_of_ride(user, ride)
        assert user.current_ride_id is None

    def test_multiple_users_multiple_vehicles(self, fleet_system):
        """Test multiple users renting different vehicles simultaneously."""
        fm = fleet_system['fleet_manager']
        user1 = fleet_system['user1']
        user2 = fleet_system['user2']
        bike = fleet_system['bike']
        ebike = fleet_system['ebike']
        scooter = fleet_system['scooter']
        station1 = fleet_system['station1']

        # User 1 rents bike
        user1.current_ride_id = "RIDE001"
        bike.rent()
        station1.remove_vehicle("BIKE001")
        assert bike.status == "rented"

        # User 2 rents ebike
        user2.current_ride_id = "RIDE002"
        ebike.rent()
        station1.remove_vehicle("EBIKE001")
        assert ebike.status == "rented"

        # Both vehicles are rented
        assert bike.status == "rented"
        assert ebike.status == "rented"
        assert scooter.status == "available"

        # Verify station has correct count
        assert len(station1.vehicles) == 1  # Only scooter left

    def test_vehicle_degradation_and_treatment(self, fleet_system):
        """Test vehicle degradation tracking and treatment."""
        fm = fleet_system['fleet_manager']
        station1 = fleet_system['station1']
        bike = fleet_system['bike']
        ebike = fleet_system['ebike']

        # Bike has 3 rides, increment to 7
        bike.rides_since_last_treated = 7
        bike.return_vehicle(1)
        assert bike.status == "degraded"

        # Treat the bike
        bike.treat()
        assert bike.status == "available"
        assert bike.rides_since_last_treated == 0
        assert bike.last_treated_date == date.today()

        # E-bike treatment with battery
        ebike.status = "degraded"
        ebike.rides_since_last_treated = 8
        ebike.battery_level = 25

        ebike.treat()
        assert ebike.status == "available"
        assert ebike.rides_since_last_treated == 0
        assert ebike.battery_level == 100

    def test_station_capacity_management(self, fleet_system):
        """Test station capacity constraints."""
        fm = fleet_system['fleet_manager']
        station2 = fleet_system['station2']

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
        fm = fleet_system['fleet_manager']
        ebike = fleet_system['ebike']
        scooter = fleet_system['scooter']

        # Ebike with full battery should rent
        ebike.battery_level = 100
        ebike.rent()
        assert ebike.status == "rented"

        # Reset for next test
        ebike.status = "available"
        ebike.station_id = 1

        # Scooter with low battery shouldn't rent
        scooter.battery_level = 15  # Below 20% threshold
        with pytest.raises(Exception, match="Electric vehicle is not available for rent"):
            scooter.rent()

        # After charging, should rent
        scooter.battery_level = 100
        scooter.rent()
        assert scooter.status == "rented"

    def test_fleet_manager_state_management(self, fleet_system):
        """Test FleetManager maintains correct state."""
        fm = fleet_system['fleet_manager']
        user1 = fleet_system['user1']
        station1 = fleet_system['station1']
        bike = fleet_system['bike']

        # Create a ride and add to active rides
        ride = Ride(
            ride_id="RIDE001",
            user_id="USER001",
            vehicle_id="BIKE001"
        )
        fm.active_rides["RIDE001"] = ride

        # Verify all state dictionaries
        assert len(fm.stations) >= 2
        assert len(fm.users) >= 2
        assert len(fm.active_rides) >= 1

        # Verify retrieval
        retrieved_ride = fm.active_rides.get("RIDE001")
        assert retrieved_ride is not None
        assert retrieved_ride.user_id == "USER001"

        # Process end of ride
        process_end_of_ride(user1, ride)

        # Clean up active ride
        del fm.active_rides["RIDE001"]
        assert "RIDE001" not in fm.active_rides

    def test_ride_cost_calculation_integration(self, fleet_system):
        """Test ride cost calculation in complete scenarios."""
        user = fleet_system['user1']

        # Normal ride
        normal_ride = Ride(
            ride_id="RIDE_NORMAL",
            user_id="USER001",
            vehicle_id="BIKE001",
            is_degraded_report=False
        )
        assert normal_ride.calculate_cost() == 15

        # Degraded ride
        degraded_ride = Ride(
            ride_id="RIDE_DEGRADED",
            user_id="USER001",
            vehicle_id="BIKE001",
            is_degraded_report=True
        )
        assert degraded_ride.calculate_cost() == 0

        # User should be charged correctly
        initial_state = user.current_ride_id

        user.current_ride_id = "RIDE_NORMAL"
        process_end_of_ride(user, normal_ride)
        assert user.current_ride_id is None

        user.current_ride_id = "RIDE_DEGRADED"
        process_end_of_ride(user, degraded_ride)
        assert user.current_ride_id is None

    def test_station_with_distance_functionality(self, fleet_system):
        """Test StationWithDistance for nearest station queries."""
        station1 = fleet_system['station1']

        # Create stations with distances
        nearby_station = StationWithDistance(
            station_id=1,
            name="Central Station",
            lat=32.0,
            lon=34.0,
            max_capacity=20,
            vehicles=["BIKE001"],
            distance=0.5
        )
        far_station = StationWithDistance(
            station_id=2,
            name="Far Station",
            lat=32.5,
            lon=34.5,
            max_capacity=15,
            vehicles=["BIKE002"],
            distance=5.0
        )

        # Verify distance comparison
        assert nearby_station.distance < far_station.distance

        # Both should have functionality
        assert nearby_station.has_available_vehicle() is True
        assert far_station.has_available_vehicle() is True

        # Can add/remove vehicles
        nearby_station.add_vehicle("BIKE003")
        assert len(nearby_station.vehicles) == 2

        nearby_station.remove_vehicle("BIKE001")
        assert len(nearby_station.vehicles) == 1

    def test_complete_system_workflow(self, fleet_system):
        """Test a complete workflow through the system."""
        fm = fleet_system['fleet_manager']
        user = fleet_system['user1']
        station1 = fleet_system['station1']
        station2 = fleet_system['station2']
        bike = fleet_system['bike']

        # 1. User registers (already done in fixture)
        assert user.user_id in fm.users
        assert user.can_start_ride() is True

        # 2. Find nearest station (simplified - just check stations exist)
        assert 1 in fm.stations
        assert 2 in fm.stations

        # 3. Select vehicle and start ride
        user.current_ride_id = "TRIP001"
        assert user.can_start_ride() is False

        bike.rent()
        assert bike.status == "rented"
        station1.remove_vehicle("BIKE001")

        # 4. Ride in progress
        assert bike.status == "rented"
        assert user.current_ride_id == "TRIP001"

        # 5. End ride at different station
        bike.return_vehicle(2)
        station2.add_vehicle("BIKE001")

        # 6. Process payment
        ride = Ride(
            ride_id="TRIP001",
            user_id="USER001",
            vehicle_id="BIKE001",
            is_degraded_report=False
        )
        process_end_of_ride(user, ride)

        # 7. Verify final state
        assert user.current_ride_id is None
        assert bike.status == "available"
        assert bike.station_id == 2
        assert "BIKE001" in station2.vehicles
        assert "BIKE001" not in station1.vehicles


class TestErrorHandlingIntegration:
    """Integration tests for error handling across models."""

    def test_invalid_operations_are_caught(self):
        """Test that invalid operations raise appropriate errors."""
        bike = Bicycle(
            vehicle_id="BIKE_ERR",
            station_id=1,
            vehicle_type="bike",
            status="degraded",
            rides_since_last_treated=0,
            last_treated_date=date.today()
        )

        # Can't rent degraded vehicle
        with pytest.raises(Exception):
            bike.rent()

        # Station overflow
        station = Station(
            station_id=99,
            name="Small Station",
            lat=32.0,
            lon=34.0,
            max_capacity=1,
            vehicles=["V001"]
        )

        with pytest.raises(Exception):
            station.add_vehicle("V002")

        # Invalid user charging
        user = User(user_id="INVALID", payment_token="")
        with pytest.raises(ValueError):
            user.charge(15)

    def test_state_consistency_across_operations(self):
        """Test that state remains consistent across multiple operations."""
        user = User(user_id="CONSISTENCY_TEST", payment_token="tok_123")
        station = Station(
            station_id=1,
            name="Consistency Station",
            lat=32.0,
            lon=34.0,
            max_capacity=5,
            vehicles=[]
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

        # User ride state
        assert user.can_start_ride() is True
        user.current_ride_id = "R1"
        assert user.can_start_ride() is False
        user.current_ride_id = None
        assert user.can_start_ride() is True

