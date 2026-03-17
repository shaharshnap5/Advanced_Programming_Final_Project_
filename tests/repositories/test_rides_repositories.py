from __future__ import annotations

import pytest
from unittest.mock import AsyncMock, Mock, MagicMock

from src.repositories.stations_repository import StationsRepository
from src.repositories.users_repository import UsersRepository
from src.repositories.vehicles_repository import VehiclesRepository


# ============ StationsRepository Tests ============


@pytest.mark.asyncio
async def test_list_with_capacity():
    """Test getting all stations with their current capacity count."""
    repo = StationsRepository()

    # Mock database cursor
    mock_cursor = AsyncMock()
    mock_cursor.fetchall = AsyncMock(
        return_value=[
            {"station_id": 1, "name": "Station 1", "lat": 32.0, "lon": 34.0, "max_capacity": 10, "current_capacity": 5},
            {"station_id": 2, "name": "Station 2", "lat": 32.1, "lon": 34.1, "max_capacity": 15, "current_capacity": 0},
        ]
    )
    mock_cursor.close = AsyncMock()

    mock_db = AsyncMock()
    mock_db.execute = AsyncMock(return_value=mock_cursor)

    result = await repo.list_with_capacity(mock_db)

    assert len(result) == 2
    assert result[0]["station_id"] == 1
    assert result[0]["current_capacity"] == 5
    assert result[1]["station_id"] == 2
    assert result[1]["current_capacity"] == 0
    mock_cursor.close.assert_called_once()


# ============ UsersRepository Tests ============


@pytest.mark.asyncio
async def test_update_current_ride_id():
    """Test updating a user's current_ride_id."""
    repo = UsersRepository()

    mock_cursor = AsyncMock()
    mock_cursor.rowcount = 1
    mock_cursor.close = AsyncMock()

    mock_db = AsyncMock()
    mock_db.execute = AsyncMock(return_value=mock_cursor)
    mock_db.commit = AsyncMock()

    result = await repo.update_current_ride_id(mock_db, "USER001", "RIDE001")

    assert result is True
    mock_db.execute.assert_called_once()
    mock_db.commit.assert_called_once()
    mock_cursor.close.assert_called_once()


@pytest.mark.asyncio
async def test_update_current_ride_id_to_none():
    """Test clearing a user's current_ride_id."""
    repo = UsersRepository()

    mock_cursor = AsyncMock()
    mock_cursor.rowcount = 1
    mock_cursor.close = AsyncMock()

    mock_db = AsyncMock()
    mock_db.execute = AsyncMock(return_value=mock_cursor)
    mock_db.commit = AsyncMock()

    result = await repo.update_current_ride_id(mock_db, "USER001", None)

    assert result is True
    mock_db.execute.assert_called_once()
    mock_db.commit.assert_called_once()


@pytest.mark.asyncio
async def test_list_active_users():
    """Test getting all users with active rides."""
    repo = UsersRepository()

    mock_cursor = AsyncMock()
    mock_cursor.fetchall = AsyncMock(
        return_value=[
            {"user_id": "USER001"},
            {"user_id": "USER002"},
        ]
    )
    mock_cursor.close = AsyncMock()

    mock_db = AsyncMock()
    mock_db.execute = AsyncMock(return_value=mock_cursor)

    result = await repo.list_active_users(mock_db)

    assert len(result) == 2
    assert result[0]["user_id"] == "USER001"
    assert result[1]["user_id"] == "USER002"
    mock_cursor.close.assert_called_once()


@pytest.mark.asyncio
async def test_list_active_users_empty():
    """Test getting active users when none exist."""
    repo = UsersRepository()

    mock_cursor = AsyncMock()
    mock_cursor.fetchall = AsyncMock(return_value=[])
    mock_cursor.close = AsyncMock()

    mock_db = AsyncMock()
    mock_db.execute = AsyncMock(return_value=mock_cursor)

    result = await repo.list_active_users(mock_db)

    assert result == []


# ============ VehiclesRepository Tests ============


@pytest.mark.asyncio
async def test_dock_vehicle():
    """Test docking a vehicle after a ride ends."""
    repo = VehiclesRepository()

    mock_cursor = AsyncMock()
    mock_cursor.rowcount = 1
    mock_cursor.close = AsyncMock()

    mock_db = AsyncMock()
    mock_db.execute = AsyncMock(return_value=mock_cursor)
    mock_db.commit = AsyncMock()

    result = await repo.dock_vehicle(
        mock_db,
        vehicle_id="VEH001",
        station_id=1,
        rides_since_last_treated=6,
        status="available",
    )

    assert result is True
    mock_db.execute.assert_called_once()
    mock_db.commit.assert_called_once()
    mock_cursor.close.assert_called_once()

    # Verify the SQL query was called with correct parameters
    call_args = mock_db.execute.call_args
    assert "VEH001" in call_args[0][1]
    assert 1 in call_args[0][1]
    assert 6 in call_args[0][1]
    assert "available" in call_args[0][1]


@pytest.mark.asyncio
async def test_dock_vehicle_degraded_status():
    """Test docking a vehicle with degraded status."""
    repo = VehiclesRepository()

    mock_cursor = AsyncMock()
    mock_cursor.rowcount = 1
    mock_cursor.close = AsyncMock()

    mock_db = AsyncMock()
    mock_db.execute = AsyncMock(return_value=mock_cursor)
    mock_db.commit = AsyncMock()

    result = await repo.dock_vehicle(
        mock_db,
        vehicle_id="VEH001",
        station_id=2,
        rides_since_last_treated=11,
        status="degraded",
    )

    assert result is True
    call_args = mock_db.execute.call_args
    assert "degraded" in call_args[0][1]


@pytest.mark.asyncio
async def test_dock_vehicle_no_match():
    """Test dock_vehicle when vehicle does not exist."""
    repo = VehiclesRepository()

    mock_cursor = AsyncMock()
    mock_cursor.rowcount = 0  # No vehicles updated
    mock_cursor.close = AsyncMock()

    mock_db = AsyncMock()
    mock_db.execute = AsyncMock(return_value=mock_cursor)
    mock_db.commit = AsyncMock()

    result = await repo.dock_vehicle(
        mock_db,
        vehicle_id="NONEXISTENT",
        station_id=1,
        rides_since_last_treated=5,
        status="available",
    )

    assert result is False
