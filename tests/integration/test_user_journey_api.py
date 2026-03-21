from __future__ import annotations

import pytest
import pytest_asyncio
import aiosqlite
from httpx import AsyncClient, ASGITransport

from db.schema import CREATE_SQL
from src.main import app
from src.controllers import users_controller, rides_controller, vehicles_controller, stations_controller


@pytest_asyncio.fixture
async def isolated_api_client() -> AsyncClient:
    db = await aiosqlite.connect(":memory:")
    db.row_factory = aiosqlite.Row
    await db.executescript(CREATE_SQL)

    # Seed stations
    await db.execute(
        "INSERT INTO stations (station_id, name, lat, lon, max_capacity) VALUES (?, ?, ?, ?, ?)",
        (1, "Station One", 32.0, 34.0, 10),
    )
    await db.execute(
        "INSERT INTO stations (station_id, name, lat, lon, max_capacity) VALUES (?, ?, ?, ?, ?)",
        (2, "Station Two", 32.1, 34.1, 10),
    )

    # Seed vehicles
    await db.execute(
        "INSERT INTO vehicles (vehicle_id, station_id, vehicle_type, status, rides_since_last_treated, last_treated_date) VALUES (?, ?, ?, ?, ?, ?)",
        ("BICYCLE_001", 1, "bicycle", "available", 0, "2026-01-01"),
    )
    await db.execute(
        "INSERT INTO vehicles (vehicle_id, station_id, vehicle_type, status, rides_since_last_treated, last_treated_date) VALUES (?, ?, ?, ?, ?, ?)",
        ("SCOOTER_001", 2, "scooter", "available", 1, "2026-01-01"),
    )
    await db.execute(
        "INSERT INTO scooters (vehicle_id, battery) VALUES (?, ?)",
        ("SCOOTER_001", 100),
    )
    await db.execute(
        "INSERT INTO vehicles (vehicle_id, station_id, vehicle_type, status, rides_since_last_treated, last_treated_date) VALUES (?, ?, ?, ?, ?, ?)",
        ("BICYCLE_TREAT_001", None, "bicycle", "degraded", 12, "2026-01-01"),
    )
    await db.commit()

    async def override_get_db():
        yield db

    original_overrides = dict(app.dependency_overrides)
    app.dependency_overrides[users_controller.get_db] = override_get_db
    app.dependency_overrides[rides_controller.get_db] = override_get_db
    app.dependency_overrides[vehicles_controller.get_db] = override_get_db
    app.dependency_overrides[stations_controller.get_db] = override_get_db

    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        yield client

    app.dependency_overrides = original_overrides
    await db.close()


@pytest.mark.asyncio
async def test_full_user_journey_register_start_end_and_station_capacity(isolated_api_client: AsyncClient):
    # Register a user
    register_response = await isolated_api_client.post(
        "/users/register",
        json={
            "user_id": "USER_JOURNEY_001",
            "first_name": "Journey",
            "last_name": "User",
            "email": "journey@example.com",
        },
    )
    assert register_response.status_code == 201

    station_1_before = await isolated_api_client.get("/stations/1")
    station_2_before = await isolated_api_client.get("/stations/2")
    assert station_1_before.status_code == 200
    assert station_2_before.status_code == 200

    station_1_before_vehicles = station_1_before.json()["vehicles"]
    station_2_before_vehicles = station_2_before.json()["vehicles"]
    assert "BICYCLE_001" in station_1_before_vehicles

    # Start ride - should remove picked vehicle from source station lock spots
    start_response = await isolated_api_client.post(
        "/rides/start",
        json={"user_id": "USER_JOURNEY_001", "lon": 34.0, "lat": 32.0},
    )
    assert start_response.status_code == 200
    started_ride = start_response.json()

    station_1_after_start = await isolated_api_client.get("/stations/1")
    assert station_1_after_start.status_code == 200
    station_1_after_start_vehicles = station_1_after_start.json()["vehicles"]
    assert started_ride["vehicle_id"] not in station_1_after_start_vehicles
    assert len(station_1_after_start_vehicles) == len(station_1_before_vehicles) - 1

    active_users_response = await isolated_api_client.get("/rides/active-users")
    assert active_users_response.status_code == 200
    active_user_ids = {row["user_id"] for row in active_users_response.json()}
    assert "USER_JOURNEY_001" in active_user_ids

    # End ride - should dock to station 2 and charge fixed 15 ILS
    end_response = await isolated_api_client.post(
        "/rides/end",
        json={"ride_id": started_ride["ride_id"], "lon": 34.1, "lat": 32.1},
    )
    assert end_response.status_code == 200
    end_payload = end_response.json()
    assert end_payload["end_station_id"] == 2
    assert end_payload["payment_charged"] == 15

    station_2_after = await isolated_api_client.get("/stations/2")
    assert station_2_after.status_code == 200
    station_2_after_vehicles = station_2_after.json()["vehicles"]
    assert started_ride["vehicle_id"] in station_2_after_vehicles
    assert len(station_2_after_vehicles) == len(station_2_before_vehicles) + 1


@pytest.mark.asyncio
async def test_api_endpoints_contract_happy_path(isolated_api_client: AsyncClient):
    register_response = await isolated_api_client.post(
        "/users/register",
        json={
            "user_id": "USER_API_001",
            "first_name": "Api",
            "last_name": "User",
            "email": "api@example.com",
        },
    )
    assert register_response.status_code == 201
    assert register_response.json()["user"]["user_id"] == "USER_API_001"

    nearest_response = await isolated_api_client.get("/stations/nearest?lon=34.0&lat=32.0")
    assert nearest_response.status_code == 200
    assert "station_id" in nearest_response.json()

    start_response = await isolated_api_client.post(
        "/rides/start",
        json={"user_id": "USER_API_001", "lon": 34.0, "lat": 32.0},
    )
    assert start_response.status_code == 200
    ride_id = start_response.json()["ride_id"]
    rented_vehicle_id = start_response.json()["vehicle_id"]

    active_users_response = await isolated_api_client.get("/rides/active-users")
    assert active_users_response.status_code == 200
    assert any(user["user_id"] == "USER_API_001" for user in active_users_response.json())

    end_response = await isolated_api_client.post(
        "/rides/end",
        json={"ride_id": ride_id, "lon": 34.1, "lat": 32.1},
    )
    assert end_response.status_code == 200
    assert end_response.json()["payment_charged"] == 15

    report_degraded_response = await isolated_api_client.post(f"/vehicles/{rented_vehicle_id}/report-degraded")
    assert report_degraded_response.status_code == 200
    assert report_degraded_response.json()["status"] == "degraded"

    treat_response = await isolated_api_client.post("/vehicles/BICYCLE_TREAT_001/treat?station_id=1")
    assert treat_response.status_code == 200
    assert treat_response.json()["status"] == "available"
    assert treat_response.json()["station_id"] == 1


@pytest.mark.asyncio
async def test_error_state_global_and_business_handlers(isolated_api_client: AsyncClient):
    # 400: invalid register payload shape
    bad_register_response = await isolated_api_client.post("/users/register", json={})
    assert bad_register_response.status_code == 400

    # 404: global route-not-found handler
    route_not_found_response = await isolated_api_client.get("/definitely-not-a-real-route")
    assert route_not_found_response.status_code == 404
    assert route_not_found_response.json()["error"] == "Not Found"

    # 409: reporting already-degraded vehicle again
    first_report = await isolated_api_client.post("/vehicles/BICYCLE_TREAT_001/report-degraded")
    assert first_report.status_code == 409

    # 404: resource-level not found still preserved by global 404 handler
    missing_station_response = await isolated_api_client.get("/stations/999")
    assert missing_station_response.status_code == 404
    assert missing_station_response.json()["detail"] == "Station not found"
