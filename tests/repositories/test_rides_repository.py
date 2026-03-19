"""Tests for RidesRepository."""

from __future__ import annotations

import pytest
from datetime import datetime

from src.repositories.rides_repository import RidesRepository


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

    active_user_ids = await repo.get_active_user_ids(test_db)
    assert active_user_ids == ["USER_ACTIVE"]

