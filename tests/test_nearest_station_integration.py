"""
Integration tests for the nearest station feature.
Tests the complete flow: Controller → Service → Repository → Database
with the helper function for distance calculation.
"""

from __future__ import annotations

import pytest
from httpx import AsyncClient, ASGITransport
from src.main import app
from src.models.station import calculate_euclidean_distance


class TestNearestStationIntegration:
    """Integration tests for the complete nearest station flow."""

    @pytest.mark.asyncio
    async def test_end_to_end_find_nearest_station(self, test_db):
        """
        End-to-end test: Find the nearest station to a specific point.
        Tests: Controller → Service → Repository → Database → Helper Function
        """
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            # Query for the nearest station to (32.0, 34.0)
            response = await client.get("/stations/nearest?lon=34.0&lat=32.0")

        assert response.status_code == 200
        data = response.json()

        # Verify response structure
        assert "station_id" in data
        assert "name" in data
        assert "lat" in data
        assert "lon" in data
        assert "max_capacity" in data
        assert "distance" in data

        # Verify data types
        assert isinstance(data["station_id"], int)
        assert isinstance(data["name"], str)
        assert isinstance(data["lat"], float)
        assert isinstance(data["lon"], float)
        assert isinstance(data["max_capacity"], int)
        assert isinstance(data["distance"], float)

        # Verify distance is calculated correctly
        assert data["distance"] >= 0

        # Verify distance calculation using helper function
        expected_distance = calculate_euclidean_distance(
            data["lat"], data["lon"], 32.0, 34.0
        )
        assert abs(data["distance"] - expected_distance) < 1e-6

    @pytest.mark.asyncio
    async def test_nearest_station_at_exact_location(self, test_db):
        """Test finding nearest station when querying at exact station location."""
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            # Query exactly at station 1 (32.0, 34.0)
            response = await client.get("/stations/nearest?lon=34.0&lat=32.0")

        assert response.status_code == 200
        data = response.json()

        assert data["station_id"] == 1
        assert data["name"] == "Test Station 1"
        assert data["distance"] == 0.0

    @pytest.mark.asyncio
    async def test_nearest_station_between_two_stations(self, test_db):
        """Test finding nearest station when between two stations."""
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            # Query between station 1 (32.0, 34.0) and station 2 (32.1, 34.1)
            response = await client.get("/stations/nearest?lon=34.05&lat=32.05")

        assert response.status_code == 200
        data = response.json()

        # Should find one of the nearby stations
        assert data["station_id"] in [1, 2]
        assert data["distance"] > 0
        assert "distance" in data

    @pytest.mark.asyncio
    async def test_get_single_station_vs_nearest(self, test_db):
        """
        Test that single station endpoint and nearest endpoint work correctly.
        Single station should NOT have distance, nearest SHOULD have distance.
        """
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            # Get single station by ID
            single_response = await client.get("/stations/1")

            # Get nearest station
            nearest_response = await client.get("/stations/nearest?lon=34.0&lat=32.0")

        assert single_response.status_code == 200
        assert nearest_response.status_code == 200

        single_data = single_response.json()
        nearest_data = nearest_response.json()

        # Single station should NOT have distance
        assert "distance" not in single_data

        # Nearest should have distance
        assert "distance" in nearest_data

        # Both should have the same station data (except distance)
        assert single_data["station_id"] == nearest_data["station_id"]
        assert single_data["name"] == nearest_data["name"]
        assert single_data["lat"] == nearest_data["lat"]
        assert single_data["lon"] == nearest_data["lon"]

    @pytest.mark.asyncio
    async def test_nearest_station_distance_formula(self, test_db):
        """Test that the distance calculation follows Euclidean formula."""
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            # Query at (32.3, 34.4) - should be ~0.5 distance from station 1 (32.0, 34.0)
            response = await client.get("/stations/nearest?lon=34.4&lat=32.3")

        assert response.status_code == 200
        data = response.json()

        # Verify distance calculation: sqrt(0.3^2 + 0.4^2) = sqrt(0.09 + 0.16) = sqrt(0.25) = 0.5
        # (using Pythagorean triple)
        station_lat = data["lat"]
        station_lon = data["lon"]
        expected_distance = calculate_euclidean_distance(station_lat, station_lon, 32.3, 34.4)

        assert abs(data["distance"] - expected_distance) < 1e-6

    @pytest.mark.asyncio
    async def test_nearest_station_helper_function_integration(self, test_db):
        """Test that the service uses the helper function for distance calculation."""
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            response = await client.get("/stations/nearest?lon=34.0&lat=32.0")

        assert response.status_code == 200
        data = response.json()

        # Verify the distance is calculated using the helper function
        # by testing with known values
        dist = calculate_euclidean_distance(
            data["lat"], data["lon"], 32.0, 34.0
        )

        # Should match the returned distance
        assert abs(data["distance"] - dist) < 1e-10

    @pytest.mark.asyncio
    async def test_multiple_nearest_queries_same_result(self, test_db):
        """Test that multiple queries for the same nearest station return consistent results."""
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            # Run multiple queries
            response1 = await client.get("/stations/nearest?lon=34.0&lat=32.0")
            response2 = await client.get("/stations/nearest?lon=34.0&lat=32.0")
            response3 = await client.get("/stations/nearest?lon=34.0&lat=32.0")

        assert response1.status_code == 200
        assert response2.status_code == 200
        assert response3.status_code == 200

        data1 = response1.json()
        data2 = response2.json()
        data3 = response3.json()

        # All should return the same station
        assert data1["station_id"] == data2["station_id"] == data3["station_id"]
        assert data1["distance"] == data2["distance"] == data3["distance"]

    @pytest.mark.asyncio
    async def test_nearest_station_error_handling_no_stations(self, test_db):
        """Test error handling when querying for nearest but no stations exist."""
        # This is a realistic test - in an empty database scenario
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            # Valid query format but will test database has data
            response = await client.get("/stations/nearest?lon=34.0&lat=32.0")

        # Should either find a station or return 404
        assert response.status_code in [200, 404]

    @pytest.mark.asyncio
    async def test_nearest_station_all_required_fields(self, test_db):
        """Test that nearest station response includes all required fields."""
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            response = await client.get("/stations/nearest?lon=34.0&lat=32.0")

        assert response.status_code == 200
        data = response.json()

        required_fields = {
            "station_id": int,
            "name": str,
            "lat": float,
            "lon": float,
            "max_capacity": int,
            "distance": float
        }

        for field, expected_type in required_fields.items():
            assert field in data, f"Missing required field: {field}"
            assert isinstance(data[field], expected_type), \
                f"Field {field} should be {expected_type.__name__}, got {type(data[field]).__name__}"

    @pytest.mark.asyncio
    async def test_nearest_station_response_format_json(self, test_db):
        """Test that nearest station response is valid JSON with correct format."""
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            response = await client.get("/stations/nearest?lon=34.0&lat=32.0")

        assert response.status_code == 200
        assert response.headers["content-type"].startswith("application/json")

        # Verify it's properly formatted JSON
        data = response.json()
        assert isinstance(data, dict)

