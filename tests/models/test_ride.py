"""
Comprehensive tests for the Ride model with 100% coverage.
Tests cover:
- Normal ride cost calculation
- Degraded ride cost calculation
- Process end of ride functionality
"""

import pytest
from unittest.mock import Mock, patch
from datetime import date

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
            is_degraded_report=False
        )

    @pytest.fixture
    def degraded_ride(self):
        """Create a degraded Ride instance for testing."""
        return Ride(
            ride_id="RIDE002",
            user_id="USER002",
            vehicle_id="VEHICLE002",
            is_degraded_report=True
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
            vehicle_id="VEHICLE003"
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
        ride1 = Ride(ride_id="R1", user_id="U1", vehicle_id="V1", is_degraded_report=False)
        ride2 = Ride(ride_id="R2", user_id="U2", vehicle_id="V2", is_degraded_report=True)

        assert ride1.ride_id != ride2.ride_id
        assert ride1.calculate_cost() == 15
        assert ride2.calculate_cost() == 0


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
            is_degraded_report=False
        )

    @pytest.fixture
    def degraded_ride(self):
        """Create a degraded Ride for testing."""
        return Ride(
            ride_id="RIDE002",
            user_id="USER002",
            vehicle_id="VEHICLE002",
            is_degraded_report=True
        )

    def test_process_end_of_ride_normal_ride(self, mock_user, normal_ride):
        """Test processing the end of a normal ride charges the user 15 ILS."""
        mock_user.current_ride_id = "RIDE001"

        process_end_of_ride(mock_user, normal_ride)

        # Verify user was charged 15 ILS
        mock_user.charge.assert_called_once_with(15)
        # Verify current_ride_id was cleared
        assert mock_user.current_ride_id is None

    def test_process_end_of_ride_degraded_ride(self, mock_user, degraded_ride):
        """Test processing the end of a degraded ride charges the user 0 ILS."""
        mock_user.current_ride_id = "RIDE002"

        process_end_of_ride(mock_user, degraded_ride)

        # Verify user was charged 0 ILS
        mock_user.charge.assert_called_once_with(0)
        # Verify current_ride_id was cleared
        assert mock_user.current_ride_id is None

    def test_process_end_of_ride_clears_current_ride(self, mock_user, normal_ride):
        """Test that current_ride_id is cleared after processing."""
        mock_user.current_ride_id = "RIDE001"
        initial_ride_id = mock_user.current_ride_id

        process_end_of_ride(mock_user, normal_ride)

        assert mock_user.current_ride_id is None

    def test_process_end_of_ride_calls_charge_method(self, mock_user, normal_ride):
        """Test that the charge method is called with the correct amount."""
        process_end_of_ride(mock_user, normal_ride)

        mock_user.charge.assert_called()
        assert mock_user.charge.call_count == 1

    def test_process_end_of_ride_with_multiple_rides(self, mock_user):
        """Test processing multiple rides in sequence."""
        ride1 = Ride(ride_id="R1", user_id="U1", vehicle_id="V1", is_degraded_report=False)
        ride2 = Ride(ride_id="R2", user_id="U2", vehicle_id="V2", is_degraded_report=True)

        mock_user.current_ride_id = "R1"
        process_end_of_ride(mock_user, ride1)

        mock_user.current_ride_id = "R2"
        process_end_of_ride(mock_user, ride2)

        assert mock_user.charge.call_count == 2
        # First call with 15, second call with 0
        calls = mock_user.charge.call_args_list
        assert calls[0][0][0] == 15
        assert calls[1][0][0] == 0

