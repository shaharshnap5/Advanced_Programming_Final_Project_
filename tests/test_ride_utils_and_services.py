from __future__ import annotations

import pytest
from unittest.mock import AsyncMock, Mock

from src.utils.distance import euclidean_distance
from src.services.stations_service import StationsService
from src.repositories.stations_repository import StationsRepository


# ============ Distance Utility Tests ============


def test_euclidean_distance_same_point():
    """Test distance when both points are the same."""
    dist = euclidean_distance(32.0, 34.0, 32.0, 34.0)
    assert dist == 0.0


def test_euclidean_distance_simple():
    """Test distance with simple values."""
    dist = euclidean_distance(0.0, 0.0, 3.0, 4.0)
    assert dist == 5.0  # 3-4-5 right triangle


def test_euclidean_distance_negative():
    """Test distance with negative coordinates."""
    dist = euclidean_distance(-32.0, -34.0, -32.0, -30.0)
    assert dist == 4.0


def test_euclidean_distance_precision():
    """Test distance with floating point precision."""
    dist = euclidean_distance(32.5, 34.5, 32.3, 34.7)
    expected = ((32.5 - 32.3) ** 2 + (34.5 - 34.7) ** 2) ** 0.5
    assert abs(dist - expected) < 1e-10


# ============ StationsService Tests ============


@pytest.mark.asyncio
async def test_get_nearest_station_with_capacity():
    """Test finding nearest station with available capacity."""
    mock_repo = AsyncMock(spec=StationsRepository)

    stations_data = [
        {
            "station_id": 1,
            "name": "Station 1",
            "lat": 32.0,
            "lon": 34.0,
            "max_capacity": 10,
            "current_capacity": 5,
        },
        {
            "station_id": 2,
            "name": "Station 2",
            "lat": 32.5,
            "lon": 34.5,
            "max_capacity": 10,
            "current_capacity": 9,
        },
        {
            "station_id": 3,
            "name": "Station 3",
            "lat": 32.1,
            "lon": 34.1,
            "max_capacity": 5,
            "current_capacity": 5,  # Full, should be filtered out
        },
    ]

    mock_repo.list_with_capacity = AsyncMock(return_value=stations_data)

    service = StationsService(repository=mock_repo)
    mock_db = Mock()

    result = await service.get_nearest_station_with_capacity(
        mock_db, lon=34.0, lat=32.0
    )

    # Station 1 should be selected (closest and has capacity)
    assert result is not None
    assert result.station_id == 1


@pytest.mark.asyncio
async def test_get_nearest_station_with_capacity_no_available():
    """Test when no station has available capacity."""
    mock_repo = AsyncMock(spec=StationsRepository)

    stations_data = [
        {
            "station_id": 1,
            "name": "Station 1",
            "lat": 32.0,
            "lon": 34.0,
            "max_capacity": 10,
            "current_capacity": 10,  # Full
        },
        {
            "station_id": 2,
            "name": "Station 2",
            "lat": 32.5,
            "lon": 34.5,
            "max_capacity": 10,
            "current_capacity": 10,  # Full
        },
    ]

    mock_repo.list_with_capacity = AsyncMock(return_value=stations_data)

    service = StationsService(repository=mock_repo)
    mock_db = Mock()

    result = await service.get_nearest_station_with_capacity(
        mock_db, lon=34.0, lat=32.0
    )

    assert result is None


@pytest.mark.asyncio
async def test_get_nearest_station_with_capacity_empty():
    """Test when no stations exist."""
    mock_repo = AsyncMock(spec=StationsRepository)
    mock_repo.list_with_capacity = AsyncMock(return_value=[])

    service = StationsService(repository=mock_repo)
    mock_db = Mock()

    result = await service.get_nearest_station_with_capacity(
        mock_db, lon=34.0, lat=32.0
    )

    assert result is None


@pytest.mark.asyncio
async def test_get_nearest_station_with_capacity_picks_closest():
    """Test that nearest station is correctly identified by euclidean distance."""
    mock_repo = AsyncMock(spec=StationsRepository)

    stations_data = [
        {
            "station_id": 1,
            "name": "Far Station",
            "lat": 32.0,
            "lon": 34.0,
            "max_capacity": 10,
            "current_capacity": 5,
        },
        {
            "station_id": 2,
            "name": "Close Station",
            "lat": 32.1,
            "lon": 34.1,
            "max_capacity": 10,
            "current_capacity": 5,
        },
    ]

    mock_repo.list_with_capacity = AsyncMock(return_value=stations_data)

    service = StationsService(repository=mock_repo)
    mock_db = Mock()

    # User location close to Station 2
    result = await service.get_nearest_station_with_capacity(
        mock_db, lon=34.1, lat=32.1
    )

    assert result is not None
    assert result.station_id == 2  # Closest one should be selected
