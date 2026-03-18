"""Integration tests for the complete Ride flow."""

from __future__ import annotations

import pytest
from datetime import datetime

from src.models.ride import Ride, process_end_of_ride
from src.models.user import User


@pytest.mark.asyncio
async def test_complete_ride_lifecycle_integration(test_db):
    """Test a complete ride lifecycle from creation to completion."""
    # Setup: Create a user and ride
    user = User(
        user_id="USER_INTEGRATION",
        first_name="Integration",
        last_name="User",
        email="user.integration@example.com",
        payment_token="TEST_TOKEN_123"
    )

    # Create a ride
    ride = Ride(
        ride_id="RIDE_INTEGRATION_001",
        user_id="USER_INTEGRATION",
        vehicle_id="V_INTEGRATION",
        start_station_id=1,
        start_time=datetime(2026, 3, 17, 10, 0),
        is_degraded_report=False
    )

    # Verify ride was created properly
    assert ride.ride_id == "RIDE_INTEGRATION_001"
    assert ride.user_id == "USER_INTEGRATION"
    assert ride.vehicle_id == "V_INTEGRATION"
    assert ride.start_station_id == 1
    assert ride.start_time == datetime(2026, 3, 17, 10, 0)
    assert ride.end_time is None
    assert ride.is_degraded_report is False

    # Calculate cost
    cost = ride.calculate_cost()
    assert cost == 15  # Normal ride

    # User starts the ride
    assert user.can_start_ride() is True

    # End the ride and process
    process_end_of_ride(user, ride)


@pytest.mark.asyncio
async def test_degraded_ride_lifecycle_integration(test_db):
    """Test a degraded ride lifecycle."""
    # Setup: Create a user and degraded ride
    user = User(
        user_id="USER_DEGRADED",
        first_name="Degraded",
        last_name="User",
        email="user.degraded@example.com",
        payment_token="TEST_TOKEN_456"
    )

    # Create a degraded ride
    ride = Ride(
        ride_id="RIDE_DEGRADED_001",
        user_id="USER_DEGRADED",
        vehicle_id="V_DEGRADED",
        start_station_id=2,
        start_time=datetime(2026, 3, 17, 11, 0),
        is_degraded_report=True  # Marked as degraded
    )

    # Verify degraded status
    assert ride.is_degraded_report is True

    # Calculate cost (should be 0 for degraded)
    cost = ride.calculate_cost()
    assert cost == 0

    # User ends the ride
    process_end_of_ride(user, ride)


@pytest.mark.asyncio
async def test_multiple_sequential_rides(test_db):
    """Test multiple sequential rides for the same user."""
    user = User(
        user_id="USER_SEQUENTIAL",
        first_name="Sequential",
        last_name="User",
        email="user.sequential@example.com",
        payment_token="TEST_TOKEN_789"
    )

    rides = [
        Ride(
            ride_id=f"RIDE_SEQ_{i}",
            user_id="USER_SEQUENTIAL",
            vehicle_id=f"V_SEQ_{i}",
            start_station_id=i + 1,
            start_time=datetime(2026, 3, 17, 10 + i, 0),
            is_degraded_report=i % 2 == 1  # Every other ride degraded
        )
        for i in range(3)
    ]

    # Process all rides
    for ride in rides:
        assert user.can_start_ride() is True

        cost = ride.calculate_cost()
        if ride.is_degraded_report:
            assert cost == 0
        else:
            assert cost == 15

        process_end_of_ride(user, ride)


@pytest.mark.asyncio
async def test_ride_model_with_end_time_integration():
    """Test a ride that has both start and end times."""
    ride = Ride(
        ride_id="RIDE_COMPLETE",
        user_id="USER_COMPLETE",
        vehicle_id="V_COMPLETE",
        start_station_id=1,
        start_time=datetime(2026, 3, 17, 10, 0),
        end_time=datetime(2026, 3, 17, 10, 30),
        is_degraded_report=False
    )

    # Verify both times are set
    assert ride.start_time is not None
    assert ride.end_time is not None
    assert ride.end_time > ride.start_time

    # Calculate duration (for potential future use)
    duration = ride.end_time - ride.start_time
    assert duration.total_seconds() == 1800  # 30 minutes


@pytest.mark.asyncio
async def test_ride_serialization_roundtrip():
    """Test that a ride can be serialized and would be deserializable."""
    original_ride = Ride(
        ride_id="RIDE_SERIALIZE",
        user_id="USER_SERIALIZE",
        vehicle_id="V_SERIALIZE",
        start_station_id=3,
        start_time=datetime(2026, 3, 17, 12, 0),
        end_time=datetime(2026, 3, 17, 12, 45),
        is_degraded_report=False
    )

    # Serialize to dict
    ride_dict = original_ride.model_dump()

    # Verify all fields are present
    assert ride_dict['ride_id'] == "RIDE_SERIALIZE"
    assert ride_dict['user_id'] == "USER_SERIALIZE"
    assert ride_dict['vehicle_id'] == "V_SERIALIZE"
    assert ride_dict['start_station_id'] == 3
    assert ride_dict['is_degraded_report'] is False

    # Recreate from dict
    recreated_ride = Ride(**ride_dict)
    assert recreated_ride.ride_id == original_ride.ride_id
    assert recreated_ride.user_id == original_ride.user_id
    assert recreated_ride.calculate_cost() == original_ride.calculate_cost()

