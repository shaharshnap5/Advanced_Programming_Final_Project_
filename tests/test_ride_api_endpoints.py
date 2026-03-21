from __future__ import annotations

import pytest


async def _create_user_record(test_db, user_id: str) -> None:
    await test_db.execute(
        """
        INSERT INTO users (user_id, payment_token, current_ride_id)
        VALUES (?, ?, ?)
        """,
        (user_id, "tok_test_001", None),
    )
    await test_db.commit()


@pytest.mark.asyncio
async def test_register_endpoint_success(test_db, isolated_client):
    response = await isolated_client.post(
        "/register",
        json={"name": "API User", "credit_token": "tok_register_001"},
    )

    assert response.status_code == 200
    assert "user_id" in response.json()


@pytest.mark.asyncio
async def test_ride_start_endpoint_success(test_db, isolated_client):
    await _create_user_record(test_db, "ride-start-user")

    response = await isolated_client.post(
        "/ride/start",
        json={"user_id": "ride-start-user", "lat": 32.0, "lon": 34.0},
    )

    assert response.status_code == 200
    assert "ride_id" in response.json()


@pytest.mark.asyncio
async def test_ride_end_endpoint_success(test_db, isolated_client):
    await _create_user_record(test_db, "ride-end-user")

    start_response = await isolated_client.post(
        "/ride/start",
        json={"user_id": "ride-end-user", "lat": 32.0, "lon": 34.0},
    )

    ride_id = start_response.json().get("ride_id")
    response = await isolated_client.post(
        "/ride/end",
        json={"ride_id": ride_id, "lat": 32.1, "lon": 34.1},
    )

    assert start_response.status_code == 200
    assert response.status_code == 200
    assert "payment_charged" in response.json()
