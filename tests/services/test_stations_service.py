from __future__ import annotations

import pytest
from unittest.mock import AsyncMock, Mock

from src.services.stations_service import StationsService
from src.repositories.stations_repository import StationsRepository
from src.models.station import calculate_euclidean_distance


# ============================================================================
# Tests for get_station_by_id
# ============================================================================

@pytest.mark.asyncio
async def test_get_station_by_id_success():
    """Test successfully retrieving a station by ID."""
    mock_repo = Mock(spec=StationsRepository)
    mock_repo.get_by_id = AsyncMock(return_value={
        "station_id": 1,
        "name": "Test Station",
        "lat": 32.0,
        "lon": 34.0,
        "max_capacity": 10
    })

    service = StationsService(repository=mock_repo)
    mock_db = Mock()

    result = await service.get_station_by_id(mock_db, 1)

    assert result is not None
    assert result["station_id"] == 1
    assert result["name"] == "Test Station"
    assert result["lat"] == 32.0
    assert result["lon"] == 34.0
    mock_repo.get_by_id.assert_called_once_with(mock_db, 1)


@pytest.mark.asyncio
async def test_get_station_by_id_not_found():
    """Test retrieving a non-existent station returns None."""
    mock_repo = Mock(spec=StationsRepository)
    mock_repo.get_by_id = AsyncMock(return_value=None)

    service = StationsService(repository=mock_repo)
    mock_db = Mock()

    result = await service.get_station_by_id(mock_db, 999)

    assert result is None
    mock_repo.get_by_id.assert_called_once_with(mock_db, 999)


# ============================================================================
# Tests for get_nearest_station with helper function
# ============================================================================

@pytest.mark.asyncio
async def test_get_nearest_station_success():
    """Test getting nearest station and distance calculation via helper function."""
    mock_repo = Mock(spec=StationsRepository)
    mock_repo.get_nearest = AsyncMock(return_value={
        "station_id": 1,
        "name": "Nearest Station",
        "lat": 32.0,
        "lon": 34.0,
        "max_capacity": 10
    })

    service = StationsService(repository=mock_repo)
    mock_db = Mock()

    result = await service.get_nearest_station(mock_db, lon=34.0, lat=32.0)

    assert result is not None
    assert result["station_id"] == 1
    assert result["name"] == "Nearest Station"
    assert "distance" in result

    # Verify distance is calculated using helper function
    expected_distance = calculate_euclidean_distance(32.0, 34.0, 32.0, 34.0)
    assert result["distance"] == expected_distance
    assert result["distance"] == 0.0  # Same point = 0 distance

    mock_repo.get_nearest.assert_called_once_with(mock_db, lon=34.0, lat=32.0)


@pytest.mark.asyncio
async def test_get_nearest_station_calculates_distance_correctly():
    """Test that distance is correctly calculated using helper function."""
    mock_repo = Mock(spec=StationsRepository)
    mock_repo.get_nearest = AsyncMock(return_value={
        "station_id": 1,
        "name": "Station 1",
        "lat": 32.0,
        "lon": 34.0,
        "max_capacity": 10
    })

    service = StationsService(repository=mock_repo)
    mock_db = Mock()

    # Query from a different location
    result = await service.get_nearest_station(mock_db, lon=34.3, lat=32.4)

    assert result is not None
    assert "distance" in result

    # Verify the distance calculation is correct (Pythagorean: 3-4-5)
    # lat: 32.0 to 32.4 = 0.4
    # lon: 34.0 to 34.3 = 0.3
    # distance = sqrt(0.4^2 + 0.3^2) = sqrt(0.16 + 0.09) = sqrt(0.25) = 0.5
    expected_distance = calculate_euclidean_distance(32.0, 34.0, 32.4, 34.3)
    assert result["distance"] == expected_distance
    assert result["distance"] == pytest.approx(0.5)


@pytest.mark.asyncio
async def test_get_nearest_station_not_found():
    """Test get_nearest_station when no station exists."""
    mock_repo = Mock(spec=StationsRepository)
    mock_repo.get_nearest = AsyncMock(return_value=None)

    service = StationsService(repository=mock_repo)
    mock_db = Mock()

    result = await service.get_nearest_station(mock_db, lon=34.0, lat=32.0)

    assert result is None
    mock_repo.get_nearest.assert_called_once_with(mock_db, lon=34.0, lat=32.0)


@pytest.mark.asyncio
async def test_get_nearest_station_with_different_locations():
    """Test nearest station with various location combinations."""
    mock_repo = Mock(spec=StationsRepository)

    test_cases = [
        # (station_lat, station_lon, query_lat, query_lon, expected_distance)
        (32.0, 34.0, 32.0, 34.0, 0.0),  # Same point
        (32.0, 34.0, 32.3, 34.4, 0.5),  # 3-4-5 triangle
        (0.0, 0.0, 3.0, 4.0, 5.0),      # Another 3-4-5 triangle
        (40.7128, -74.0060, 40.7128, -74.0060, 0.0),  # NYC coordinates (same)
    ]

    for station_lat, station_lon, query_lat, query_lon, expected_dist in test_cases:
        mock_repo.get_nearest = AsyncMock(return_value={
            "station_id": 1,
            "name": "Test Station",
            "lat": station_lat,
            "lon": station_lon,
            "max_capacity": 10
        })

        service = StationsService(repository=mock_repo)
        mock_db = Mock()

        result = await service.get_nearest_station(mock_db, lon=query_lon, lat=query_lat)

        assert result is not None
        assert abs(result["distance"] - expected_dist) < 1e-10


# ============================================================================
# Tests for the helper function: calculate_euclidean_distance
# ============================================================================

def test_calculate_euclidean_distance_same_point():
    """Test distance between same point is zero."""
    distance = calculate_euclidean_distance(32.0, 34.0, 32.0, 34.0)
    assert distance == 0.0


def test_calculate_euclidean_distance_pythagorean_triple():
    """Test with Pythagorean triple: 3-4-5."""
    distance = calculate_euclidean_distance(0, 0, 3, 4)
    assert distance == 5.0


def test_calculate_euclidean_distance_another_pythagorean():
    """Test with another Pythagorean triple: 5-12-13."""
    distance = calculate_euclidean_distance(0, 0, 5, 12)
    assert distance == 13.0


def test_calculate_euclidean_distance_symmetry():
    """Test that distance(A, B) == distance(B, A)."""
    d1 = calculate_euclidean_distance(32.0, 34.0, 32.1, 34.1)
    d2 = calculate_euclidean_distance(32.1, 34.1, 32.0, 34.0)
    assert d1 == d2


def test_calculate_euclidean_distance_negative_coordinates():
    """Test with negative coordinates."""
    distance = calculate_euclidean_distance(-3, -4, 0, 0)
    assert distance == 5.0


def test_calculate_euclidean_distance_triangle_inequality():
    """Test triangle inequality: d(A,C) <= d(A,B) + d(B,C)."""
    lat1, lon1 = 32.0, 34.0
    lat2, lon2 = 32.1, 34.1
    lat3, lon3 = 32.2, 34.2

    d12 = calculate_euclidean_distance(lat1, lon1, lat2, lon2)
    d23 = calculate_euclidean_distance(lat2, lon2, lat3, lon3)
    d13 = calculate_euclidean_distance(lat1, lon1, lat3, lon3)

    # Triangle inequality: d13 <= d12 + d23 (with floating point tolerance)
    assert d13 <= d12 + d23 + 1e-10


def test_calculate_euclidean_distance_returns_positive():
    """Test that distance is always non-negative."""
    test_cases = [
        (0, 0, 10, 10),
        (-5, -5, 5, 5),
        (1.5, 2.5, 3.5, 4.5),
    ]

    for lat1, lon1, lat2, lon2 in test_cases:
        distance = calculate_euclidean_distance(lat1, lon1, lat2, lon2)
        assert distance >= 0, "Distance should never be negative"


def test_calculate_euclidean_distance_with_floats():
    """Test with floating-point coordinates."""
    distance = calculate_euclidean_distance(32.123, 34.456, 32.456, 34.789)
    assert isinstance(distance, float)
    assert distance > 0

