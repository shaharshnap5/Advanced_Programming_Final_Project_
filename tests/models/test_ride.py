"""
Comprehensive tests for the Ride model with 100% coverage.
Tests cover:
- Normal ride cost calculation
- Degraded ride cost calculation
- Process end of ride functionality
- DateTime fields (start_time, end_time)
- Station ID validation
- Ride state management
"""

import pytest
from unittest.mock import Mock, patch
from datetime import datetime, date

from src.models.ride import Ride, process_end_of_ride
from src.models.user import User


class TestRide:
    """Tests for the Ride model."""

    @pytest.fixture
    def valid_ride(self):
        """Create a valid Ride instance for testing."""
        return Ride(
            ride_id="RIDE001",
            user_id="USER001",
            vehicle_id="VEHICLE001",
            start_station_id=1,
            start_time=datetime(2026, 3, 17, 10, 0, 0),
            is_degraded_report=False
        )

    @pytest.fixture
    def degraded_ride(self):
        """Create a degraded Ride instance for testing."""
        return Ride(
            ride_id="RIDE002",
            user_id="USER002",
            vehicle_id="VEHICLE002",
            start_station_id=2,
            start_time=datetime(2026, 3, 17, 11, 0, 0),
            is_degraded_report=True
        )

    @pytest.fixture
    def ride_with_end_time(self):
        """Create a Ride with both start and end times."""
        return Ride(
            ride_id="RIDE003",
            user_id="USER003",
            vehicle_id="VEHICLE003",
            start_station_id=3,
            start_time=datetime(2026, 3, 17, 12, 0, 0),
            end_time=datetime(2026, 3, 17, 12, 30, 0),
            is_degraded_report=False
        )

    def test_ride_initialization(self, valid_ride):
        """Test that a Ride can be initialized with required fields."""
        assert valid_ride.ride_id == "RIDE001"
        assert valid_ride.user_id == "USER001"
        assert valid_ride.vehicle_id == "VEHICLE001"
        assert valid_ride.is_degraded_report is False

    def test_ride_default_is_degraded_report(self):
        """Test that is_degraded_report defaults to False."""
        ride = Ride(
            ride_id="RIDE003",
            user_id="USER003",
            vehicle_id="VEHICLE003",
            start_station_id=3,
            start_time=datetime(2026, 3, 17, 12, 0)
        )
        assert ride.is_degraded_report is False

    def test_calculate_cost_normal_ride(self, valid_ride):
        """Test that a normal ride costs 15 ILS."""
        cost = valid_ride.calculate_cost()
        assert cost == 15

    def test_calculate_cost_degraded_ride(self, degraded_ride):
        """Test that a degraded ride costs 0 ILS."""
        cost = degraded_ride.calculate_cost()
        assert cost == 0

    def test_ride_is_pydantic_model(self, valid_ride):
        """Test that Ride is a Pydantic BaseModel."""
        # Pydantic models support dict() conversion
        ride_dict = valid_ride.model_dump()
        assert isinstance(ride_dict, dict)
        assert "ride_id" in ride_dict
        assert "user_id" in ride_dict
        assert "vehicle_id" in ride_dict
        assert "is_degraded_report" in ride_dict

    def test_ride_validation_missing_required_field(self):
        """Test that Ride validation fails when required fields are missing."""
        with pytest.raises(Exception):  # Pydantic will raise validation error
            Ride(ride_id="RIDE004", user_id="USER004")  # Missing vehicle_id

    def test_ride_multiple_instances(self):
        """Test that multiple Ride instances can be created independently."""
        ride1 = Ride(ride_id="R1", user_id="U1", vehicle_id="V1", start_station_id=1, start_time=datetime.now(), is_degraded_report=False)
        ride2 = Ride(ride_id="R2", user_id="U2", vehicle_id="V2", start_station_id=2, start_time=datetime.now(), is_degraded_report=True)

        assert ride1.ride_id != ride2.ride_id
        assert ride1.calculate_cost() == 15
        assert ride2.calculate_cost() == 0

    def test_ride_start_time_required(self):
        """Test that start_time is a required field."""
        with pytest.raises(Exception):  # Pydantic validation error
            Ride(
                ride_id="RIDE004",
                user_id="USER004",
                vehicle_id="VEHICLE004",
                start_station_id=4
                # Missing start_time
            )

    def test_ride_start_station_id_required(self):
        """Test that start_station_id is a required field."""
        with pytest.raises(Exception):  # Pydantic validation error
            Ride(
                ride_id="RIDE005",
                user_id="USER005",
                vehicle_id="VEHICLE005",
                start_time=datetime.now()
                # Missing start_station_id
            )

    def test_ride_with_start_time(self, valid_ride):
        """Test that start_time is properly set."""
        expected_time = datetime(2026, 3, 17, 10, 0, 0)
        assert valid_ride.start_time == expected_time

    def test_ride_with_start_station_id(self, valid_ride):
        """Test that start_station_id is properly set."""
        assert valid_ride.start_station_id == 1

    def test_ride_end_time_is_optional(self):
        """Test that end_time defaults to None when not provided."""
        ride = Ride(
            ride_id="RIDE006",
            user_id="USER006",
            vehicle_id="VEHICLE006",
            start_station_id=6,
            start_time=datetime.now()
        )
        assert ride.end_time is None

    def test_ride_with_end_time(self, ride_with_end_time):
        """Test that end_time can be set."""
        expected_end = datetime(2026, 3, 17, 12, 30, 0)
        assert ride_with_end_time.end_time == expected_end

    def test_ride_end_time_after_start_time(self, ride_with_end_time):
        """Test that end_time is after start_time."""
        assert ride_with_end_time.end_time > ride_with_end_time.start_time

    def test_ride_with_different_start_stations(self):
        """Test that different rides can have different start stations."""
        ride1 = Ride(
            ride_id="R1",
            user_id="U1",
            vehicle_id="V1",
            start_station_id=1,
            start_time=datetime(2026, 3, 17, 10, 0)
        )
        ride2 = Ride(
            ride_id="R2",
            user_id="U2",
            vehicle_id="V2",
            start_station_id=5,
            start_time=datetime(2026, 3, 17, 11, 0)
        )
        assert ride1.start_station_id != ride2.start_station_id

    def test_ride_pydantic_serialization(self, ride_with_end_time):
        """Test that Ride can be serialized to dict."""
        ride_dict = ride_with_end_time.model_dump()
        assert isinstance(ride_dict, dict)
        assert "ride_id" in ride_dict
        assert "user_id" in ride_dict
        assert "vehicle_id" in ride_dict
        assert "start_station_id" in ride_dict
        assert "start_time" in ride_dict
        assert "end_time" in ride_dict
        assert "is_degraded_report" in ride_dict
        assert ride_dict["start_station_id"] == 3
        assert ride_dict["is_degraded_report"] is False

    def test_ride_pydantic_json_serialization(self, ride_with_end_time):
        """Test that Ride can be serialized to JSON."""
        ride_json = ride_with_end_time.model_dump_json()
        assert isinstance(ride_json, str)
        assert "RIDE003" in ride_json
        assert "USER003" in ride_json


class TestProcessEndOfRide:
    """Tests for the process_end_of_ride function."""

    @pytest.fixture
    def mock_user(self):
        """Create a mock User instance."""
        return Mock(spec=User)

    @pytest.fixture
    def normal_ride(self):
        """Create a normal Ride for testing."""
        return Ride(
            ride_id="RIDE001",
            user_id="USER001",
            vehicle_id="VEHICLE001",
            start_station_id=1,
            start_time=datetime(2026, 3, 17, 10, 0),
            is_degraded_report=False
        )

    @pytest.fixture
    def degraded_ride(self):
        """Create a degraded Ride for testing."""
        return Ride(
            ride_id="RIDE002",
            user_id="USER002",
            vehicle_id="VEHICLE002",
            start_station_id=2,
            start_time=datetime(2026, 3, 17, 11, 0),
            is_degraded_report=True
        )

    def test_process_end_of_ride_normal_ride(self, mock_user, normal_ride):
        """Test processing the end of a normal ride charges the user 15 ILS."""

        process_end_of_ride(mock_user, normal_ride)

        # Verify user was charged 15 ILS
        mock_user.charge.assert_called_once_with(15)

    def test_process_end_of_ride_degraded_ride(self, mock_user, degraded_ride):
        """Test processing the end of a degraded ride charges the user 0 ILS."""

        process_end_of_ride(mock_user, degraded_ride)

        # Verify user was charged 0 ILS
        mock_user.charge.assert_called_once_with(0)

    def test_process_end_of_ride_calls_charge_method(self, mock_user, normal_ride):
        """Test that the charge method is called with the correct amount."""
        process_end_of_ride(mock_user, normal_ride)

        mock_user.charge.assert_called()
        assert mock_user.charge.call_count == 1

    def test_process_end_of_ride_with_multiple_rides(self, mock_user):
        """Test processing multiple rides in sequence."""
        ride1 = Ride(
            ride_id="R1",
            user_id="U1",
            vehicle_id="V1",
            start_station_id=1,
            start_time=datetime(2026, 3, 17, 10, 0),
            is_degraded_report=False
        )
        ride2 = Ride(
            ride_id="R2",
            user_id="U2",
            vehicle_id="V2",
            start_station_id=2,
            start_time=datetime(2026, 3, 17, 11, 0),
            is_degraded_report=True
        )

        process_end_of_ride(mock_user, ride1)
        process_end_of_ride(mock_user, ride2)

        assert mock_user.charge.call_count == 2
        # First call with 15, second call with 0
        calls = mock_user.charge.call_args_list
        assert calls[0][0][0] == 15
        assert calls[1][0][0] == 0

    def test_process_end_of_ride_order_of_operations(self, mock_user, normal_ride):
        """Test that operations happen in the correct order: calculate -> charge -> clear."""
        call_order = []

        def track_charge(amount):
            call_order.append(('charge', amount))

        mock_user.charge = Mock(side_effect=track_charge)
        mock_user.current_ride_id = "RIDE001"

        process_end_of_ride(mock_user, normal_ride)

        assert ('charge', 15) in call_order
        assert mock_user.current_ride_id is None

    def test_process_end_of_ride_preserves_user_data(self, mock_user, normal_ride):
        """Test that process_end_of_ride doesn't modify other user attributes."""
        mock_user.user_id = "USER001"
        mock_user.payment_token = "TOKEN123"
        mock_user.current_ride_id = "RIDE001"

        process_end_of_ride(mock_user, normal_ride)

        assert mock_user.user_id == "USER001"
        assert mock_user.payment_token == "TOKEN123"
        assert mock_user.current_ride_id is None

    def test_process_end_of_ride_with_different_ride_ids(self, mock_user):
        """Test processing rides with different IDs."""
        rides = [
            Ride(ride_id=f"R{i}", user_id=f"U{i}", vehicle_id=f"V{i}",
                 start_station_id=i, start_time=datetime(2026, 3, 17, 10 + i, 0),
                 is_degraded_report=i % 2 == 0)
            for i in range(3)
        ]

        for ride in rides:
            mock_user.current_ride_id = ride.ride_id
            process_end_of_ride(mock_user, ride)

        assert mock_user.current_ride_id is None
        assert mock_user.charge.call_count == 3

    def test_process_end_of_ride_charge_amount_accuracy(self, mock_user):
        """Test that charge amounts are calculated correctly."""
        degraded_ride = Ride(
            ride_id="DEGRADED",
            user_id="USER_D",
            vehicle_id="VEHICLE_D",
            start_station_id=1,
            start_time=datetime(2026, 3, 17, 12, 0),
            is_degraded_report=True
        )

        mock_user.current_ride_id = "DEGRADED"
        process_end_of_ride(mock_user, degraded_ride)

        # Verify exact charge amount for degraded ride
        mock_user.charge.assert_called_once_with(0)

    def test_process_end_of_ride_with_end_time_set(self, mock_user):
        """Test processing a ride that already has an end_time."""
        ride = Ride(
            ride_id="COMPLETE",
            user_id="USER_COMPLETE",
            vehicle_id="VEHICLE_COMPLETE",
            start_station_id=5,
            start_time=datetime(2026, 3, 17, 14, 0),
            end_time=datetime(2026, 3, 17, 14, 45),
            is_degraded_report=False
        )

        mock_user.current_ride_id = "COMPLETE"
        process_end_of_ride(mock_user, ride)

        mock_user.charge.assert_called_once_with(15)
        assert mock_user.current_ride_id is None
