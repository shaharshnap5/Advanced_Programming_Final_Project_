from __future__ import annotations

import pytest


async def _get_vehicle_count(test_db, station_id: int) -> int:
    cursor = await test_db.execute(
        "SELECT COUNT(*) AS vehicle_count FROM vehicles WHERE station_id = ?",
        (station_id,),
    )
    row = await cursor.fetchone()
    await cursor.close()
    return row["vehicle_count"]


@pytest.mark.asyncio
async def test_register_start_ride_end_ride_flow(test_db, isolated_client):
    source_station_id = 1
    destination_station_id = 2
    source_vehicle_count_before = await _get_vehicle_count(test_db, source_station_id)
    destination_vehicle_count_before = await _get_vehicle_count(test_db, destination_station_id)

    register_response = await isolated_client.post(
        "/register",
        json={"name": "Ride Flow User", "credit_token": "tok_ride_flow_001"},
    )

    assert register_response.status_code == 200
    user_id = register_response.json()["user_id"]

    start_response = await isolated_client.post(
        "/ride/start",
        json={"user_id": user_id, "lat": 32.0, "lon": 34.0},
    )

    assert start_response.status_code == 200
    ride_id = start_response.json().get("ride_id")
    source_vehicle_count_after_start = await _get_vehicle_count(test_db, source_station_id)

    assert source_vehicle_count_after_start == source_vehicle_count_before - 1

    end_response = await isolated_client.post(
        "/ride/end",
        json={"ride_id": ride_id, "lat": 32.1, "lon": 34.1},
    )

    assert end_response.status_code == 200
    destination_vehicle_count_after_end = await _get_vehicle_count(test_db, destination_station_id)

    assert destination_vehicle_count_after_end == destination_vehicle_count_before + 1
    assert end_response.json()["payment_charged"] == 15
