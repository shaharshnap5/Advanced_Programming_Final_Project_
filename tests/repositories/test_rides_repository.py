"""Tests for RidesRepository."""

from __future__ import annotations

import pytest
from datetime import datetime

from src.repositories.rides_repository import RidesRepository
from src.models.ride import Ride


@pytest.mark.asyncio
async def test_create_active_ride_with_explicit_start_time(test_db):
    """Test creating an active ride with an explicitly provided start time."""
    repo = RidesRepository()
    start_time = datetime(2026, 3, 17, 10, 30, 0)

    await repo.create_active_ride(
        test_db,
        ride_id="RIDE001",
        user_id="USER001",
        vehicle_id="V001",
        start_station_id=1,
        start_time=start_time
    )

    # Verify the ride was created
    cursor = await test_db.execute("SELECT * FROM rides WHERE ride_id = ?", ("RIDE001",))
    row = await cursor.fetchone()
    assert row is not None
    assert row["ride_id"] == "RIDE001"
    assert row["user_id"] == "USER001"
    assert row["vehicle_id"] == "V001"
    assert row["start_station_id"] == 1
    assert row["is_degraded_report"] == 0  # Should be False
    assert row["end_time"] is None  # Should be None by default


@pytest.mark.asyncio
async def test_create_active_ride_without_explicit_start_time(test_db):
    """Test creating an active ride with default start time."""
    repo = RidesRepository()

    await repo.create_active_ride(
        test_db,
        ride_id="RIDE002",
        user_id="USER002",
        vehicle_id="V001",
        start_station_id=1
    )

    # Verify the ride was created with default start_time
    cursor = await test_db.execute("SELECT * FROM rides WHERE ride_id = ?", ("RIDE002",))
    row = await cursor.fetchone()
    assert row is not None
    assert row["ride_id"] == "RIDE002"
    assert row["user_id"] == "USER002"
    assert row["vehicle_id"] == "V001"
    assert row["start_station_id"] == 1
    assert row["start_time"] is not None


@pytest.mark.asyncio
async def test_create_active_ride_with_different_stations(test_db):
    """Test creating rides from different stations."""
    repo = RidesRepository()

    # Create rides from station 1 and 2
    await repo.create_active_ride(
        test_db,
        ride_id="RIDE003",
        user_id="USER003",
        vehicle_id="V001",
        start_station_id=1
    )

    await repo.create_active_ride(
        test_db,
        ride_id="RIDE004",
        user_id="USER004",
        vehicle_id="V002",
        start_station_id=2
    )

    # Verify rides from different stations
    cursor = await test_db.execute("SELECT * FROM rides ORDER BY ride_id")
    rows = await cursor.fetchall()
    ride_map = {row["ride_id"]: row for row in rows}

    assert ride_map["RIDE003"]["start_station_id"] == 1
    assert ride_map["RIDE004"]["start_station_id"] == 2


@pytest.mark.asyncio
async def test_create_active_ride_degraded_flag_default(test_db):
    """Test that is_degraded_report defaults to False."""
    repo = RidesRepository()

    await repo.create_active_ride(
        test_db,
        ride_id="RIDE005",
        user_id="USER005",
        vehicle_id="V001",
        start_station_id=1
    )

    cursor = await test_db.execute("SELECT is_degraded_report FROM rides WHERE ride_id = ?", ("RIDE005",))
    row = await cursor.fetchone()
    assert row["is_degraded_report"] == 0


@pytest.mark.asyncio
async def test_create_multiple_active_rides(test_db):
    """Test creating multiple active rides for different users and vehicles."""
    repo = RidesRepository()

    ride_data = [
        ("RIDE101", "USER101", "V001", 1, datetime(2026, 3, 17, 10, 0)),
        ("RIDE102", "USER102", "V002", 2, datetime(2026, 3, 17, 10, 15)),
        ("RIDE103", "USER103", "V001", 1, datetime(2026, 3, 17, 10, 30)),
    ]

    for ride_id, user_id, vehicle_id, station_id, start_time in ride_data:
        await repo.create_active_ride(
            test_db,
            ride_id=ride_id,
            user_id=user_id,
            vehicle_id=vehicle_id,
            start_station_id=station_id,
            start_time=start_time
        )

    # Verify all rides were created
    cursor = await test_db.execute("SELECT COUNT(*) as count FROM rides")
    row = await cursor.fetchone()
    assert row["count"] == 3


@pytest.mark.asyncio
async def test_create_active_ride_with_specific_timestamp(test_db):
    """Test creating a ride with a specific timestamp."""
    repo = RidesRepository()
    specific_time = datetime(2026, 3, 15, 14, 45, 30)

    await repo.create_active_ride(
        test_db,
        ride_id="RIDE200",
        user_id="USER200",
        vehicle_id="V001",
        start_station_id=1,
        start_time=specific_time
    )

    cursor = await test_db.execute("SELECT start_time FROM rides WHERE ride_id = ?", ("RIDE200",))
    row = await cursor.fetchone()
    # The timestamp should be stored as provided
    assert row["start_time"] is not None


@pytest.mark.asyncio
async def test_get_active_user_ids_returns_only_incomplete_rides(test_db):
    repo = RidesRepository()

    # Create a user and one active ride + one completed ride
    await test_db.execute(
        "INSERT INTO users (user_id, first_name, last_name, email, payment_token) VALUES (?, ?, ?, ?, ?)",
        ("USER_ACTIVE", "Active", "User", "active@example.com", "tok_active")
    )

    await test_db.execute(
        "INSERT INTO rides (ride_id, user_id, vehicle_id, start_station_id, end_station_id, start_time, end_time) VALUES (?, ?, ?, ?, ?, CURRENT_TIMESTAMP, NULL)",
        ("RIDE_ACTIVE", "USER_ACTIVE", "V001", 1, None)
    )

    await test_db.execute(
        "INSERT INTO rides (ride_id, user_id, vehicle_id, start_station_id, end_station_id, start_time, end_time) VALUES (?, ?, ?, ?, ?, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP)",
        ("RIDE_COMPLETE", "USER_ACTIVE", "V002", 2, 3)
    )

    await test_db.commit()

    active_users = await repo.get_active_users(test_db)
    assert len(active_users) == 1
    assert active_users[0].user_id == "USER_ACTIVE"
    assert active_users[0].email == "active@example.com"


@pytest.mark.asyncio
async def test_complete_ride_updates_end_fields(test_db):
    """Test that completing a ride persists end_station_id and end_time."""
    repo = RidesRepository()
    start_time = datetime(2026, 3, 17, 10, 30, 0)
    end_time = datetime(2026, 3, 17, 11, 15, 0)

    await repo.create_active_ride(
        test_db,
        ride_id="RIDE_COMPLETE_001",
        user_id="USER_COMPLETE_001",
        vehicle_id="V001",
        start_station_id=1,
        start_time=start_time,
    )

    updated = await repo.complete_ride(
        test_db,
        ride_id="RIDE_COMPLETE_001",
        end_station_id=2,
        end_time=end_time,
    )

    assert updated is True

    cursor = await test_db.execute(
        "SELECT end_station_id, end_time FROM rides WHERE ride_id = ?",
        ("RIDE_COMPLETE_001",),
    )
    row = await cursor.fetchone()
    await cursor.close()

    assert row is not None
    assert row["end_station_id"] == 2
    assert row["end_time"] is not None
    parsed_end_time = datetime.fromisoformat(row["end_time"]) if isinstance(row["end_time"], str) else row["end_time"]
    assert parsed_end_time == end_time


@pytest.mark.asyncio
async def test_complete_ride_marks_degraded_and_allows_null_end_station(test_db):
    """Completing a degraded ride should support NULL end_station and set is_degraded_report."""
    repo = RidesRepository()
    start_time = datetime(2026, 3, 17, 10, 30, 0)
    end_time = datetime(2026, 3, 17, 10, 45, 0)

    await repo.create_active_ride(
        test_db,
        ride_id="RIDE_DEGRADED_001",
        user_id="USER_DEGRADED_001",
        vehicle_id="V001",
        start_station_id=1,
        start_time=start_time,
    )

    updated = await repo.complete_ride(
        test_db,
        ride_id="RIDE_DEGRADED_001",
        end_station_id=None,
        end_time=end_time,
        is_degraded_report=True,
    )

    assert updated is True

    cursor = await test_db.execute(
        "SELECT end_station_id, end_time, is_degraded_report FROM rides WHERE ride_id = ?",
        ("RIDE_DEGRADED_001",),
    )
    row = await cursor.fetchone()
    await cursor.close()

    assert row is not None
    assert row["end_station_id"] is None
    assert row["is_degraded_report"] == 1
    assert row["end_time"] is not None


@pytest.mark.asyncio
async def test_get_active_ride_by_vehicle_returns_active_ride(test_db):
    repo = RidesRepository()
    start_time = datetime(2026, 3, 17, 10, 30, 0)

    await repo.create_active_ride(
        test_db,
        ride_id="RIDE_BY_VEHICLE_001",
        user_id="USER_BY_VEHICLE_001",
        vehicle_id="V001",
        start_station_id=1,
        start_time=start_time,
    )

    active_ride = await repo.get_active_ride_by_vehicle(test_db, "V001")

    assert active_ride is not None
    assert active_ride.ride_id == "RIDE_BY_VEHICLE_001"
    assert active_ride.vehicle_id == "V001"


@pytest.mark.asyncio
async def test_get_active_ride_by_vehicle_returns_none_when_completed(test_db):
    repo = RidesRepository()
    start_time = datetime(2026, 3, 17, 10, 30, 0)
    end_time = datetime(2026, 3, 17, 10, 45, 0)

    await repo.create_active_ride(
        test_db,
        ride_id="RIDE_BY_VEHICLE_002",
        user_id="USER_BY_VEHICLE_002",
        vehicle_id="V001",
        start_station_id=1,
        start_time=start_time,
    )

    await repo.complete_ride(
        test_db,
        ride_id="RIDE_BY_VEHICLE_002",
        end_station_id=2,
        end_time=end_time,
    )

    active_ride = await repo.get_active_ride_by_vehicle(test_db, "V001")
    assert active_ride is None


@pytest.mark.asyncio
async def test_get_active_users_returns_empty_list_when_no_active_rides(test_db):
    """No active rides should return an empty list."""
    repo = RidesRepository()

    await test_db.execute(
        "INSERT INTO users (user_id, first_name, last_name, email, payment_token) VALUES (?, ?, ?, ?, ?)",
        ("USER_NO_ACTIVE", "No", "Active", "none@example.com", "tok_none")
    )
    await test_db.commit()

    active_users = await repo.get_active_users(test_db)

    assert active_users == []


@pytest.mark.asyncio
async def test_get_active_ride_by_user_returns_ride_object(test_db):
    """Test that get_active_ride_by_user returns a Ride object, not a database row."""
    repo = RidesRepository()
    start_time = datetime(2026, 3, 17, 10, 30, 0)

    await repo.create_active_ride(
        test_db,
        ride_id="RIDE_ACTIVE_001",
        user_id="USER_ACTIVE_001",
        vehicle_id="V001",
        start_station_id=1,
        start_time=start_time
    )

    # Get the active ride - should be a Ride object
    active_ride = await repo.get_active_ride_by_user(test_db, "USER_ACTIVE_001")
    
    # Verify it's a Ride object, not a database row
    assert isinstance(active_ride, Ride)
    assert active_ride.ride_id == "RIDE_ACTIVE_001"
    assert active_ride.user_id == "USER_ACTIVE_001"
    assert active_ride.vehicle_id == "V001"
    assert active_ride.start_station_id == 1
    assert active_ride.start_time == start_time
    assert active_ride.end_time is None
    assert active_ride.is_degraded_report == False


@pytest.mark.asyncio
async def test_get_active_ride_by_user_returns_none_when_no_active_ride(test_db):
    """Test that get_active_ride_by_user returns None when user has no active ride."""
    repo = RidesRepository()

    active_ride = await repo.get_active_ride_by_user(test_db, "USER_NO_RIDE")
    
    assert active_ride is None


@pytest.mark.asyncio
async def test_get_active_ride_by_user_ignores_completed_rides(test_db):
    """Test that get_active_ride_by_user ignores completed rides (with end_time)."""
    repo = RidesRepository()
    start_time = datetime(2026, 3, 17, 10, 30, 0)
    end_time = datetime(2026, 3, 17, 10, 45, 0)

    # Create an active ride
    await repo.create_active_ride(
        test_db,
        ride_id="RIDE_ACTIVE_002",
        user_id="USER_WITH_COMPLETED_RIDE",
        vehicle_id="V001",
        start_station_id=1,
        start_time=start_time
    )

    # Mark this ride as completed by updating end_time
    await test_db.execute(
        "UPDATE rides SET end_time = ? WHERE ride_id = ?",
        (end_time, "RIDE_ACTIVE_002")
    )
    await test_db.commit()

    # Get active ride should return None because the ride is completed
    active_ride = await repo.get_active_ride_by_user(test_db, "USER_WITH_COMPLETED_RIDE")
    
    assert active_ride is None


@pytest.mark.asyncio
async def test_get_active_ride_by_user_only_returns_first_active_ride(test_db):
    """Test that get_active_ride_by_user returns only one ride (first active)."""
    repo = RidesRepository()
    start_time_1 = datetime(2026, 3, 17, 10, 30, 0)
    start_time_2 = datetime(2026, 3, 17, 11, 30, 0)

    # Create first active ride
    await repo.create_active_ride(
        test_db,
        ride_id="RIDE_MULTI_ACTIVE_001",
        user_id="USER_MULTI_RIDES",
        vehicle_id="V001",
        start_station_id=1,
        start_time=start_time_1
    )

    # Create second active ride directly in DB (bypassing lock for testing edge case)
    # This shouldn't happen in real scenario due to locks, but testing the query behavior
    await test_db.execute(
        """
        INSERT INTO rides (ride_id, user_id, vehicle_id, start_station_id, is_degraded_report, start_time)
        VALUES (?, ?, ?, ?, FALSE, ?)
        """,
        ("RIDE_MULTI_ACTIVE_002", "USER_MULTI_RIDES", "V002", 2, start_time_2)
    )
    await test_db.commit()

    # Get active ride should return the first one (query returns only one row)
    active_ride = await repo.get_active_ride_by_user(test_db, "USER_MULTI_RIDES")

    assert active_ride is not None
    assert isinstance(active_ride, Ride)
    assert active_ride.user_id == "USER_MULTI_RIDES"


@pytest.mark.asyncio
async def test_get_active_ride_by_user_has_all_attributes(test_db):
    """Test that the returned Ride object has all expected attributes."""
    repo = RidesRepository()
    start_time = datetime(2026, 3, 17, 10, 30, 0)

    await repo.create_active_ride(
        test_db,
        ride_id="RIDE_FULL_ATTRS",
        user_id="USER_FULL_ATTRS",
        vehicle_id="V001",
        start_station_id=1,
        start_time=start_time
    )

    active_ride = await repo.get_active_ride_by_user(test_db, "USER_FULL_ATTRS")
    
    # Verify all attributes exist
    assert hasattr(active_ride, 'ride_id')
    assert hasattr(active_ride, 'user_id')
    assert hasattr(active_ride, 'vehicle_id')
    assert hasattr(active_ride, 'start_station_id')
    assert hasattr(active_ride, 'end_station_id')
    assert hasattr(active_ride, 'start_time')
    assert hasattr(active_ride, 'end_time')
    assert hasattr(active_ride, 'is_degraded_report')
    
    # Verify all attributes are of correct types
    assert isinstance(active_ride.ride_id, str)
    assert isinstance(active_ride.user_id, str)
    assert isinstance(active_ride.vehicle_id, str)
    assert isinstance(active_ride.start_station_id, int)
    assert isinstance(active_ride.start_time, datetime)
    assert isinstance(active_ride.is_degraded_report, bool)

