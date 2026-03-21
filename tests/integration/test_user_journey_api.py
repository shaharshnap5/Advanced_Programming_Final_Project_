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
        # Expose the in-memory DB for edge-case mutation in specific tests.
        client._test_db = db  # type: ignore[attr-defined]
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


@pytest.mark.asyncio
async def test_active_users_returns_empty_list_when_no_active_rides(isolated_api_client: AsyncClient):
    response = await isolated_api_client.get("/rides/active-users")

    assert response.status_code == 200
    assert response.json() == []


@pytest.mark.asyncio
async def test_start_ride_fails_for_unknown_user_with_404(isolated_api_client: AsyncClient):
    response = await isolated_api_client.post(
        "/rides/start",
        json={"user_id": "UNKNOWN_USER", "lon": 34.0, "lat": 32.0},
    )

    assert response.status_code == 404
    assert "not found" in response.json()["detail"].lower()


@pytest.mark.asyncio
async def test_start_ride_missing_coordinates_returns_400(isolated_api_client: AsyncClient):
    register_response = await isolated_api_client.post(
        "/users/register",
        json={
            "user_id": "USER_NO_COORDS",
            "first_name": "No",
            "last_name": "Coords",
            "email": "nocoords@example.com",
        },
    )
    assert register_response.status_code == 201

    response = await isolated_api_client.post(
        "/rides/start",
        json={"user_id": "USER_NO_COORDS"},
    )

    assert response.status_code == 400
    assert "lon" in response.json()["detail"].lower()


@pytest.mark.asyncio
async def test_start_ride_twice_for_same_user_returns_409(isolated_api_client: AsyncClient):
    register_response = await isolated_api_client.post(
        "/users/register",
        json={
            "user_id": "USER_DOUBLE_START",
            "first_name": "Double",
            "last_name": "Start",
            "email": "double.start@example.com",
        },
    )
    assert register_response.status_code == 201

    first_start = await isolated_api_client.post(
        "/rides/start",
        json={"user_id": "USER_DOUBLE_START", "lon": 34.0, "lat": 32.0},
    )
    assert first_start.status_code == 200

    second_start = await isolated_api_client.post(
        "/rides/start",
        json={"user_id": "USER_DOUBLE_START", "lon": 34.0, "lat": 32.0},
    )

    assert second_start.status_code == 409
    assert "active ride" in second_start.json()["detail"].lower()


@pytest.mark.asyncio
async def test_end_ride_unknown_ride_returns_404(isolated_api_client: AsyncClient):
    response = await isolated_api_client.post(
        "/rides/end",
        json={"ride_id": "RIDE_DOES_NOT_EXIST", "lon": 34.0, "lat": 32.0},
    )

    assert response.status_code == 404
    assert "not found" in response.json()["detail"].lower()


@pytest.mark.asyncio
async def test_end_ride_second_end_attempt_returns_409(isolated_api_client: AsyncClient):
    register_response = await isolated_api_client.post(
        "/users/register",
        json={
            "user_id": "USER_DOUBLE_END",
            "first_name": "Double",
            "last_name": "End",
            "email": "double.end@example.com",
        },
    )
    assert register_response.status_code == 201

    start_response = await isolated_api_client.post(
        "/rides/start",
        json={"user_id": "USER_DOUBLE_END", "lon": 34.0, "lat": 32.0},
    )
    assert start_response.status_code == 200
    ride_id = start_response.json()["ride_id"]

    first_end = await isolated_api_client.post(
        "/rides/end",
        json={"ride_id": ride_id, "lon": 34.1, "lat": 32.1},
    )
    assert first_end.status_code == 200

    second_end = await isolated_api_client.post(
        "/rides/end",
        json={"ride_id": ride_id, "lon": 34.1, "lat": 32.1},
    )

    assert second_end.status_code == 409
    assert "already ended" in second_end.json()["detail"].lower()


@pytest.mark.asyncio
async def test_treat_vehicle_not_eligible_returns_400(isolated_api_client: AsyncClient):
    # BICYCLE_001 starts available with low ride count, so it is not treat-eligible.
    response = await isolated_api_client.post("/vehicles/BICYCLE_001/treat")

    assert response.status_code == 400
    assert "not eligible" in response.json()["detail"].lower()


@pytest.mark.asyncio
async def test_treat_degraded_without_station_id_returns_400(isolated_api_client: AsyncClient):
    response = await isolated_api_client.post("/vehicles/BICYCLE_TREAT_001/treat")

    assert response.status_code == 400
    assert "station_id" in response.json()["detail"].lower()


@pytest.mark.asyncio
async def test_report_degraded_for_missing_vehicle_returns_404(isolated_api_client: AsyncClient):
    response = await isolated_api_client.post("/vehicles/NOT_EXISTS/report-degraded")

    assert response.status_code == 404
    assert "not found" in response.json()["detail"].lower()


@pytest.mark.asyncio
async def test_stations_nearest_missing_query_params_returns_422(isolated_api_client: AsyncClient):
    response = await isolated_api_client.get("/stations/nearest")

    assert response.status_code == 422


@pytest.mark.asyncio
async def test_start_ride_no_available_vehicles_in_system_returns_404(isolated_api_client: AsyncClient):
    register_response = await isolated_api_client.post(
        "/users/register",
        json={
            "user_id": "USER_NO_VEHICLES",
            "first_name": "No",
            "last_name": "Vehicles",
            "email": "no.vehicles@example.com",
        },
    )
    assert register_response.status_code == 201

    db = isolated_api_client._test_db  # type: ignore[attr-defined]
    await db.execute("UPDATE vehicles SET status = 'degraded'")
    await db.commit()

    response = await isolated_api_client.post(
        "/rides/start",
        json={"user_id": "USER_NO_VEHICLES", "lon": 34.0, "lat": 32.0},
    )

    assert response.status_code == 404
    assert "no available vehicles" in response.json()["detail"].lower()


@pytest.mark.asyncio
async def test_start_ride_no_eligible_vehicle_returns_409(isolated_api_client: AsyncClient):
    register_response = await isolated_api_client.post(
        "/users/register",
        json={
            "user_id": "USER_NO_ELIGIBLE",
            "first_name": "No",
            "last_name": "Eligible",
            "email": "no.eligible@example.com",
        },
    )
    assert register_response.status_code == 201

    db = isolated_api_client._test_db  # type: ignore[attr-defined]
    await db.execute("DELETE FROM scooters WHERE vehicle_id = 'SCOOTER_001'")
    await db.execute("DELETE FROM vehicles WHERE vehicle_id = 'SCOOTER_001'")
    await db.execute("UPDATE vehicles SET rides_since_last_treated = 11 WHERE vehicle_id = 'BICYCLE_001'")
    await db.commit()

    response = await isolated_api_client.post(
        "/rides/start",
        json={"user_id": "USER_NO_ELIGIBLE", "lon": 34.0, "lat": 32.0},
    )

    assert response.status_code == 409
    assert "eligibility" in response.json()["detail"].lower() or "eligible" in response.json()["detail"].lower()


@pytest.mark.asyncio
async def test_end_ride_no_station_with_capacity_returns_400(isolated_api_client: AsyncClient):
    register_response = await isolated_api_client.post(
        "/users/register",
        json={
            "user_id": "USER_NO_CAPACITY",
            "first_name": "No",
            "last_name": "Capacity",
            "email": "no.capacity@example.com",
        },
    )
    assert register_response.status_code == 201

    start_response = await isolated_api_client.post(
        "/rides/start",
        json={"user_id": "USER_NO_CAPACITY", "lon": 34.0, "lat": 32.0},
    )
    assert start_response.status_code == 200
    ride_id = start_response.json()["ride_id"]

    db = isolated_api_client._test_db  # type: ignore[attr-defined]
    # Force both stations to be effectively full for current occupancy.
    await db.execute("UPDATE stations SET max_capacity = 0 WHERE station_id = 1")
    await db.execute("UPDATE stations SET max_capacity = 1 WHERE station_id = 2")
    await db.commit()

    end_response = await isolated_api_client.post(
        "/rides/end",
        json={"ride_id": ride_id, "lon": 34.1, "lat": 32.1},
    )

    assert end_response.status_code == 400
    assert "no station with free capacity" in end_response.json()["detail"].lower()


@pytest.mark.asyncio
async def test_register_invalid_json_body_returns_400(isolated_api_client: AsyncClient):
    response = await isolated_api_client.post(
        "/users/register",
        content="{not-valid-json}",
        headers={"content-type": "application/json"},
    )

    assert response.status_code == 400
    assert response.json()["detail"] == "Invalid JSON payload"


@pytest.mark.asyncio
async def test_report_degraded_auto_ends_active_ride(isolated_api_client: AsyncClient):
    register_response = await isolated_api_client.post(
        "/users/register",
        json={
            "user_id": "USER_REPORT_FLOW",
            "first_name": "Report",
            "last_name": "Flow",
            "email": "report.flow@example.com",
        },
    )
    assert register_response.status_code == 201

    start_response = await isolated_api_client.post(
        "/rides/start",
        json={"user_id": "USER_REPORT_FLOW", "lon": 34.1, "lat": 32.1},
    )
    assert start_response.status_code == 200
    rented_vehicle_id = start_response.json()["vehicle_id"]

    report_response = await isolated_api_client.post(f"/vehicles/{rented_vehicle_id}/report-degraded")
    assert report_response.status_code == 200
    assert report_response.json()["status"] == "degraded"

    active_users_response = await isolated_api_client.get("/rides/active-users")
    assert active_users_response.status_code == 200
    assert all(user["user_id"] != "USER_REPORT_FLOW" for user in active_users_response.json())
