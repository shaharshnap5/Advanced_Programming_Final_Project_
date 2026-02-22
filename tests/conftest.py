from __future__ import annotations

import pytest
import pytest_asyncio
import aiosqlite
from pathlib import Path


@pytest_asyncio.fixture
async def test_db():
    """Create an in-memory test database with schema."""
    db = await aiosqlite.connect(":memory:")
    db.row_factory = aiosqlite.Row
    
    # Create schema
    await db.executescript("""
        CREATE TABLE stations (
          station_id INTEGER PRIMARY KEY,
          name TEXT NOT NULL,
          lat REAL NOT NULL,
          lon REAL NOT NULL,
          max_capacity INTEGER NOT NULL
        );
        
        CREATE TABLE vehicles (
          vehicle_id TEXT PRIMARY KEY,
          station_id INTEGER,
          vehicle_type TEXT NOT NULL,
          status TEXT NOT NULL,
          rides_since_last_treated INTEGER NOT NULL,
          last_treated_date TEXT,
          FOREIGN KEY(station_id) REFERENCES stations(station_id)
        );
    """)
    
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
        ("V001", 1, "bicycle", "available", 5, "2025-01-01")
    )
    await db.execute(
        "INSERT INTO vehicles (vehicle_id, station_id, vehicle_type, status, rides_since_last_treated, last_treated_date) VALUES (?, ?, ?, ?, ?, ?)",
        ("V002", 1, "scooter", "degraded", 10, "2025-01-02")
    )
    await db.commit()
    
    yield db
    
    await db.close()
