from __future__ import annotations

import pytest
import pytest_asyncio
import aiosqlite
from pathlib import Path
import sys

PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT))

from db.schema import CREATE_SQL
from src.models.vehicle import VehicleType


@pytest_asyncio.fixture
async def test_db():
    """Create an in-memory test database with schema."""
    db = await aiosqlite.connect(":memory:")
    db.row_factory = aiosqlite.Row
    
    # Create schema
    await db.executescript(CREATE_SQL)

    # Seed test data
    await db.execute(
        "INSERT INTO stations (station_id, name, lat, lon, max_capacity) VALUES (?, ?, ?, ?, ?)",
        (1, "Test Station 1", 32.0, 34.0, 10)
    )
    await db.execute(
        "INSERT INTO stations (station_id, name, lat, lon, max_capacity) VALUES (?, ?, ?, ?, ?)",
        (2, "Test Station 2", 32.1, 34.1, 20)
    )
    await db.execute(
        "INSERT INTO vehicles (vehicle_id, station_id, vehicle_type, status, rides_since_last_treated, last_treated_date) VALUES (?, ?, ?, ?, ?, ?)",
        ("V001", 1, VehicleType.bicycle.value, "available", 5, "2025-01-01")
    )
    await db.execute(
        "INSERT INTO vehicles (vehicle_id, station_id, vehicle_type, status, rides_since_last_treated, last_treated_date) VALUES (?, ?, ?, ?, ?, ?)",
        ("V002", 1, VehicleType.scooter.value, "degraded", 10, "2025-01-02")
    )
    await db.execute(
        "INSERT INTO scooters (vehicle_id, battery) VALUES (?, ?)",
        ("V002", 100),
    )
    await db.commit()
    
    yield db
    
    await db.close()
