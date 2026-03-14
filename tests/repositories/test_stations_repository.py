from __future__ import annotations

import pytest

from src.repositories.stations_repository import StationsRepository
from src.models.station import calculate_euclidean_distance


# ============================================================================
# Tests for get_by_id
# ============================================================================

@pytest.mark.asyncio
async def test_get_by_id_success(test_db):
    """Test successfully retrieving a station by ID."""
    repo = StationsRepository()
    
    station = await repo.get_by_id(test_db, 1)
    
    assert station is not None
    assert station["station_id"] == 1
    assert station["name"] == "Test Station 1"
    assert station["lat"] == 32.0
    assert station["lon"] == 34.0
    assert station["max_capacity"] == 10


@pytest.mark.asyncio
async def test_get_by_id_not_found(test_db):
    """Test retrieving a non-existent station returns None."""
    repo = StationsRepository()
    
    station = await repo.get_by_id(test_db, 999)
    
    assert station is None


# ============================================================================
# Tests for get_nearest
# ============================================================================

@pytest.mark.asyncio
async def test_get_nearest_finds_closest_station(test_db):
    """Test that get_nearest finds the closest station to a point."""
    repo = StationsRepository()
    
    # Query near station 1 (32.0, 34.0)
    station = await repo.get_nearest(test_db, lon=34.0, lat=32.0)
    
    assert station is not None
    assert station["station_id"] == 1
    assert "distance" in station
    assert isinstance(station["distance"], (int, float))


@pytest.mark.asyncio
async def test_get_nearest_returns_closest_station_2(test_db):
    """Test that querying closer to station 2 returns station 2."""
    repo = StationsRepository()
    
    # Query closer to station 2 (32.1, 34.1)
    station = await repo.get_nearest(test_db, lon=34.1, lat=32.1)
    
    assert station is not None
    assert station["station_id"] == 2
    assert "distance" in station


@pytest.mark.asyncio
async def test_get_nearest_includes_station_data(test_db):
    """Test that get_nearest returns all station fields."""
    repo = StationsRepository()

    station = await repo.get_nearest(test_db, lon=34.0, lat=32.0)

    assert station is not None
    assert "station_id" in station
    assert "name" in station
    assert "lat" in station
    assert "lon" in station
    assert "max_capacity" in station
    assert "distance" in station


@pytest.mark.asyncio
async def test_get_nearest_distance_is_non_negative(test_db):
    """Test that calculated distance is non-negative."""
    repo = StationsRepository()

    station = await repo.get_nearest(test_db, lon=34.0, lat=32.0)

    assert station is not None
    assert station["distance"] >= 0


@pytest.mark.asyncio
async def test_get_nearest_same_location_as_station(test_db):
    """Test querying at exact same location as a station."""
    repo = StationsRepository()

    # Query exactly at station 1 location
    station = await repo.get_nearest(test_db, lon=34.0, lat=32.0)

    assert station is not None
    assert station["station_id"] == 1
    # Distance should be very close to 0 (or exactly 0)
    assert station["distance"] == 0.0


@pytest.mark.asyncio
async def test_get_nearest_returns_exactly_one_station(test_db):
    """Test that get_nearest returns only one station."""
    repo = StationsRepository()

    station = await repo.get_nearest(test_db, lon=34.0, lat=32.0)

    # Should be a dict, not a list
    assert isinstance(station, dict)
    assert station["station_id"] >= 1


@pytest.mark.asyncio
async def test_get_nearest_with_various_locations(test_db):
    """Test get_nearest with different query locations."""
    repo = StationsRepository()

    test_locations = [
        (32.0, 34.0),    # Station 1 exact location
        (32.1, 34.1),    # Station 2 exact location
        (32.05, 34.05),  # Between station 1 and 2
        (32.5, 34.5),    # Far from all stations
    ]

    for lat, lon in test_locations:
        station = await repo.get_nearest(test_db, lon=lon, lat=lat)

        assert station is not None
        assert "station_id" in station
        assert "distance" in station
        assert station["distance"] >= 0


@pytest.mark.asyncio
async def test_get_nearest_consistency_with_helper_function(test_db):
    """Test that get_nearest distance calculation is consistent with helper function."""
    repo = StationsRepository()

    query_lat, query_lon = 32.0, 34.0
    station = await repo.get_nearest(test_db, lon=query_lon, lat=query_lat)

    assert station is not None

    # Calculate expected distance using helper function
    expected_distance = calculate_euclidean_distance(
        station["lat"], station["lon"], query_lat, query_lon
    )

    # Note: Repository calculates distance in SQL, which may have slight differences
    # So we use approximate equality
    assert abs(station["distance"] - expected_distance) < 1e-6


@pytest.mark.asyncio
async def test_get_nearest_returns_all_fields(test_db):
    """Test that get_nearest returns all required fields."""
    repo = StationsRepository()

    station = await repo.get_nearest(test_db, lon=34.0, lat=32.0)

    required_fields = ["station_id", "name", "lat", "lon", "max_capacity", "distance"]
    for field in required_fields:
        assert field in station, f"Missing field: {field}"

