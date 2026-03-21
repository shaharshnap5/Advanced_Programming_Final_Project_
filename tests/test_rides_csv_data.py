"""Tests for rides CSV data loading."""

import asyncio
import pytest
import sqlite3
from pathlib import Path

from scripts.init_db import init_db


@pytest.fixture(scope="module", autouse=True)
def ensure_rides_db_loaded():
    """Initialize and seed the app.db from CSV before rides CSV tests."""
    asyncio.run(init_db(reset_db=True))


@pytest.fixture
def db_path():
    """Get the path to the test database."""
    return Path(__file__).resolve().parents[1] / "data" / "app.db"


@pytest.fixture
def db_connection(db_path):
    """Create a database connection."""
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    yield conn
    conn.close()


class TestRidesCSVData:
    """Test rides CSV data loading and database operations."""

    def test_rides_table_exists(self, db_connection):
        """Test that rides table exists in the database."""
        cursor = db_connection.cursor()
        cursor.execute(
            "SELECT name FROM sqlite_master WHERE type='table' AND name='rides'"
        )
        assert cursor.fetchone() is not None

    def test_rides_data_loaded(self, db_connection):
        """Test that rides data was loaded from CSV."""
        cursor = db_connection.cursor()
        cursor.execute("SELECT COUNT(*) FROM rides")
        count = cursor.fetchone()[0]
        assert count > 0, "No rides data was loaded"

    def test_rides_count(self, db_connection):
        """Test the expected number of rides loaded."""
        cursor = db_connection.cursor()
        cursor.execute("SELECT COUNT(*) FROM rides")
        count = cursor.fetchone()[0]
        assert count == 25, f"Expected 25 rides, got {count}"

    def test_rides_columns_exist(self, db_connection):
        """Test that all required columns exist in rides table."""
        cursor = db_connection.cursor()
        cursor.execute("PRAGMA table_info(rides)")
        columns = {row[1] for row in cursor.fetchall()}
        expected_columns = {
            "ride_id",
            "user_id",
            "vehicle_id",
            "start_station_id",
            "end_station_id",
            "is_degraded_report",
            "start_time",
            "end_time",
        }
        assert expected_columns == columns

    def test_ride_has_valid_user_id(self, db_connection):
        """Test that rides reference valid users."""
        cursor = db_connection.cursor()
        cursor.execute("""
            SELECT r.ride_id, r.user_id
            FROM rides r
            LEFT JOIN users u ON r.user_id = u.user_id
            WHERE u.user_id IS NULL
            LIMIT 1
            """)
        result = cursor.fetchone()
        assert result is None, "Found ride with non-existent user"

    def test_ride_has_valid_vehicle_id(self, db_connection):
        """Test that rides reference valid vehicles."""
        cursor = db_connection.cursor()
        cursor.execute("""
            SELECT r.ride_id, r.vehicle_id
            FROM rides r
            LEFT JOIN vehicles v ON r.vehicle_id = v.vehicle_id
            WHERE v.vehicle_id IS NULL
            LIMIT 1
            """)
        result = cursor.fetchone()
        assert result is None, "Found ride with non-existent vehicle"

    def test_ride_has_valid_start_station(self, db_connection):
        """Test that rides reference valid start stations."""
        cursor = db_connection.cursor()
        cursor.execute("""
            SELECT r.ride_id, r.start_station_id
            FROM rides r
            LEFT JOIN stations s ON r.start_station_id = s.station_id
            WHERE s.station_id IS NULL
            LIMIT 1
            """)
        result = cursor.fetchone()
        assert result is None, "Found ride with non-existent start station"

    def test_ride_example(self, db_connection):
        """Test retrieving a specific ride."""
        cursor = db_connection.cursor()
        cursor.execute("""
            SELECT ride_id, user_id, vehicle_id, start_station_id, end_station_id, is_degraded_report
            FROM rides
            WHERE ride_id = 'RIDE001'
            """)
        row = cursor.fetchone()
        assert row is not None
        assert row["ride_id"] == "RIDE001"
        assert row["user_id"] == "USER001"
        assert row["vehicle_id"] == "V000001"
        assert row["start_station_id"] == 1
        assert row["end_station_id"] == 5
        assert row["is_degraded_report"] == 0

    def test_degraded_rides_exist(self, db_connection):
        """Test that degraded rides exist in the data."""
        cursor = db_connection.cursor()
        cursor.execute("SELECT COUNT(*) FROM rides WHERE is_degraded_report = 1")
        count = cursor.fetchone()[0]
        assert count > 0, "No degraded rides found"

    def test_ride_timestamps(self, db_connection):
        """Test that rides have valid timestamps."""
        cursor = db_connection.cursor()
        cursor.execute("SELECT ride_id, start_time, end_time FROM rides LIMIT 5")
        for row in cursor.fetchall():
            assert (
                row["start_time"] is not None
            ), f"Ride {row['ride_id']} has null start_time"
            # end_time can be null for ongoing rides
            if row["end_time"]:
                # Basic validation that times are in proper format
                assert ":" in row["start_time"], "Invalid timestamp format"

    def test_all_rides_have_user_and_vehicle(self, db_connection):
        """Test that all rides have associated user and vehicle."""
        cursor = db_connection.cursor()
        cursor.execute("""
            SELECT COUNT(*) FROM rides
            WHERE user_id IS NOT NULL AND vehicle_id IS NOT NULL
            """)
        count = cursor.fetchone()[0]
        assert count == 25, "Not all rides have user and vehicle"

    def test_ride_end_station_can_be_null(self, db_connection):
        """Test that end_station_id can be NULL for ongoing rides."""
        cursor = db_connection.cursor()
        cursor.execute("SELECT COUNT(*) FROM rides WHERE end_station_id IS NOT NULL")
        count = cursor.fetchone()[0]
        assert count > 0, "All rides have end_station_id set (should test nullable)"
