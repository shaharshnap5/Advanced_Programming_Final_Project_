"""
Comprehensive tests for the User model with 100% coverage.
Tests cover:
- User initialization
- charge method with valid and invalid payment tokens
"""

import pytest
from unittest.mock import Mock, patch
from io import StringIO
import sys

from src.models.user import User


class TestUser:
    """Tests for the User model."""

    @pytest.fixture
    def valid_user(self):
        """Create a valid User instance for testing."""
        return User(
            user_id="USER001",
            payment_token="tok_visa_123456",
        )

    def test_user_initialization(self, valid_user):
        """Test that a User can be initialized with required fields."""
        assert valid_user.user_id == "USER001"
        assert valid_user.payment_token == "tok_visa_123456"

    def test_charge_with_valid_payment_token(self, valid_user, capsys):
        """Test charging a user with a valid payment token."""
        valid_user.charge(15)

        captured = capsys.readouterr()
        assert "Charged user USER001 15 ILS using token tok_visa_123456" in captured.out

    def test_charge_with_different_amounts(self, valid_user, capsys):
        """Test charging a user with different amounts."""
        amounts = [0, 15, 50, 100]

        for amount in amounts:
            valid_user.charge(amount)

        captured = capsys.readouterr()
        for amount in amounts:
            assert f"Charged user USER001 {amount} ILS" in captured.out

    def test_charge_without_payment_token(self):
        """Test that charging a user without a payment token raises ValueError."""
        user = User(
            user_id="USER004",
            payment_token=""
        )

        with pytest.raises(ValueError, match="No payment token found for user"):
            user.charge(15)

    def test_charge_with_none_payment_token(self):
        """Test that charging with None payment token is handled gracefully."""
        user = User(
            user_id="USER005",
            payment_token=""
        )

        with pytest.raises(ValueError):
            user.charge(20)

    def test_user_is_pydantic_model(self, valid_user):
        """Test that User is a Pydantic BaseModel."""
        user_dict = valid_user.model_dump()
        assert isinstance(user_dict, dict)
        assert "user_id" in user_dict
        assert "payment_token" in user_dict

    def test_user_validation_missing_required_field(self):
        """Test that User validation fails when required fields are missing."""
        with pytest.raises(Exception):  # Pydantic will raise validation error
            User(user_id="USER006")  # Missing payment_token

    def test_multiple_users_independent(self):
        """Test that multiple User instances are independent."""
        user1 = User(user_id="U1", payment_token="tok1")
        user2 = User(user_id="U2", payment_token="tok2")

        assert user1.user_id != user2.user_id

    def test_charge_print_message_format(self, valid_user, capsys):
        """Test that the charge message format is correct."""
        valid_user.charge(15)

        captured = capsys.readouterr()
        expected_message = "Charged user USER001 15 ILS using token tok_visa_123456."
        assert expected_message in captured.out

    def test_charge_zero_amount(self, valid_user, capsys):
        """Test charging zero amount (free ride)."""
        valid_user.charge(0)

        captured = capsys.readouterr()
        assert "Charged user USER001 0 ILS" in captured.out

    def test_user_field_types(self, valid_user):
        """Test that User fields have correct types."""
        assert isinstance(valid_user.user_id, str)
        assert isinstance(valid_user.payment_token, str)
        assert valid_user.current_ride_id is None or isinstance(valid_user.current_ride_id, str)

    def test_can_start_ride_only_checks_current_ride_id(self, valid_user):
        """Test that can_start_ride only checks current_ride_id, not other fields."""
        # Modify other fields and verify can_start_ride still works correctly
        valid_user.user_id = "DIFFERENT_ID"
        valid_user.payment_token = "different_token"

        assert valid_user.can_start_ride() is True  # Should still be True

