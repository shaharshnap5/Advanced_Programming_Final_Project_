"""
Tests for FleetManager load_data method.
Tests data loading from CSV files and proper state initialization.
"""

import pytest
import tempfile
import os
from pathlib import Path

from src.models.FleetManager import FleetManager


class TestFleetManagerLoadData:
    """Tests for FleetManager load_data method."""

    @pytest.fixture(autouse=True)
    def reset_singleton(self):
        """Reset FleetManager singleton before each test."""
        FleetManager._instance = None
        yield
        FleetManager._instance = None

    @pytest.fixture
    def temp_stations_csv(self):
        """Create a temporary stations CSV file."""
        content = """station_id,name,lat,lon,max_capacity
1,Station_A,32.058323,34.815431,20
2,Station_B,32.135211,34.787590,15
3,Station_C,32.124426,34.771377,30
"""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False, encoding='utf-8') as f:
            f.write(content)
            temp_path = f.name
        yield temp_path
        os.unlink(temp_path)

    @pytest.fixture
    def temp_vehicles_csv(self):
        """Create a temporary vehicles CSV file."""
        content = """vehicle_id,station_id,vehicle_type,status,rides_since_last_treated,last_treated_date
V001,1,bicycle,available,3,2025-01-16
V002,1,electric_bicycle,available,0,2025-03-28
V003,2,scooter,available,5,2025-02-19
V004,2,bicycle,rented,8,2025-03-01
V005,3,electric_bicycle,degraded,11,2025-02-26
"""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False, encoding='utf-8') as f:
            f.write(content)
            temp_path = f.name
        yield temp_path
        os.unlink(temp_path)

    def test_load_data_loads_stations(self, temp_stations_csv, temp_vehicles_csv):
        """Test that load_data correctly loads stations."""
        fm = FleetManager()
        fm.load_data(temp_stations_csv, temp_vehicles_csv)

        assert len(fm.stations) == 3
        assert 1 in fm.stations
        assert 2 in fm.stations
        assert 3 in fm.stations

    def test_load_data_station_attributes(self, temp_stations_csv, temp_vehicles_csv):
        """Test that stations have correct attributes."""
        fm = FleetManager()
        fm.load_data(temp_stations_csv, temp_vehicles_csv)

        station1 = fm.stations[1]
        assert station1.station_id == 1
        assert station1.name == "Station_A"
        assert station1.lat == 32.058323
        assert station1.lon == 34.815431
        assert station1.max_capacity == 20

    def test_load_data_wires_vehicles_to_stations(self, temp_stations_csv, temp_vehicles_csv):
        """Test that vehicles are wired to their stations."""
        fm = FleetManager()
        fm.load_data(temp_stations_csv, temp_vehicles_csv)

        station1 = fm.stations[1]
        station2 = fm.stations[2]
        station3 = fm.stations[3]

        # Station 1 should have V001 and V002
        assert len(station1.vehicles) == 2
        assert "V001" in station1.vehicles
        assert "V002" in station1.vehicles

        # Station 2 should have V003 and V004
        assert len(station2.vehicles) == 2
        assert "V003" in station2.vehicles
        assert "V004" in station2.vehicles

        # Station 3 should have V005
        assert len(station3.vehicles) == 1
        assert "V005" in station3.vehicles

    def test_load_data_empty_stations(self, temp_vehicles_csv):
        """Test load_data with empty stations file."""
        content = "station_id,name,lat,lon,max_capacity\n"
        with tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False, encoding='utf-8') as f:
            f.write(content)
            empty_stations = f.name

        try:
            fm = FleetManager()
            fm.load_data(empty_stations, temp_vehicles_csv)
            assert len(fm.stations) == 0
        finally:
            os.unlink(empty_stations)

    def test_load_data_initializes_empty_vehicle_lists(self, temp_vehicles_csv):
        """Test that stations without vehicles have empty vehicle lists."""
        stations_content = """station_id,name,lat,lon,max_capacity
1,Station_A,32.058323,34.815431,20
99,Station_Empty,32.000000,34.000000,10
"""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False, encoding='utf-8') as f:
            f.write(stations_content)
            stations_path = f.name

        try:
            fm = FleetManager()
            fm.load_data(stations_path, temp_vehicles_csv)
            
            # Station 99 has no vehicles
            assert 99 in fm.stations
            assert fm.stations[99].vehicles == []
        finally:
            os.unlink(stations_path)

    def test_load_data_with_real_csv_files(self):
        """Test load_data with actual project CSV files."""
        project_root = Path(__file__).resolve().parents[2]
        stations_csv = project_root / "data" / "stations.csv"
        vehicles_csv = project_root / "data" / "vehicles.csv"

        if not stations_csv.exists() or not vehicles_csv.exists():
            pytest.skip("Real CSV files not found")

        fm = FleetManager()
        fm.load_data(str(stations_csv), str(vehicles_csv))

        # Verify data was loaded
        assert len(fm.stations) > 0
        # Verify at least one station has vehicles
        has_vehicles = any(len(station.vehicles) > 0 for station in fm.stations.values())
        assert has_vehicles
