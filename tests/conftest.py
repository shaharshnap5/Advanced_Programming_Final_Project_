from __future__ import annotations

from contextlib import ExitStack, asynccontextmanager
from pathlib import Path
import sys
from unittest.mock import patch

import aiosqlite
from httpx import ASGITransport, AsyncClient
import pytest
import pytest_asyncio

PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT))

from db.schema import CREATE_SQL
from src.main import app

try:
    from src.models.FleetManager import FleetManager
except Exception:  # pragma: no cover
    FleetManager = None


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
        ("V001", 1, "bike", "available", 5, "2025-01-01")
    )
    await db.execute(
        "INSERT INTO vehicles (vehicle_id, station_id, vehicle_type, status, rides_since_last_treated, last_treated_date) VALUES (?, ?, ?, ?, ?, ?)",
        ("V002", 1, "scooter", "degraded", 10, "2025-01-02")
    )
    await db.commit()
    
    yield db
    
    await db.close()


@pytest.fixture(autouse=True)
def reset_system_state():
    """Reset singleton state so tests do not leak model state into each other."""
    if FleetManager is not None:
        FleetManager._instance = None

    yield

    if FleetManager is not None:
        FleetManager._instance = None


@pytest_asyncio.fixture
async def isolated_client(test_db):
    """API client wired to the in-memory database for controller tests."""
    @asynccontextmanager
    async def override_db():
        yield test_db

    with ExitStack() as stack:
        for target in (
            "src.controllers.register_controller.get_db",
            "src.controllers.rides_controller.get_db",
            "src.controllers.users_controller.get_db",
            "src.controllers.stations_controller.get_db",
            "src.controllers.vehicles_controller.get_db",
            "src.controllers.vehicle_controller.get_db",
        ):
            stack.enter_context(patch(target, override_db))

        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            yield client
