from __future__ import annotations

import json
import os
import sqlite3
import subprocess
import sys
import time
import shutil
import tempfile
from pathlib import Path
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

PROJECT_ROOT = Path(__file__).resolve().parents[1]
DB_PATH = PROJECT_ROOT / "data" / "app.db"
HOST = "127.0.0.1"
PORT = 8011
BASE_URL = f"http://{HOST}:{PORT}"


class RecoveryCheckError(RuntimeError):
    pass


def _http_json(method: str, path: str, payload: dict | None = None) -> dict:
    data = None
    headers = {"Accept": "application/json"}
    if payload is not None:
        data = json.dumps(payload).encode("utf-8")
        headers["Content-Type"] = "application/json"

    request = Request(f"{BASE_URL}{path}", data=data, method=method, headers=headers)
    try:
        with urlopen(request, timeout=10) as response:
            return json.loads(response.read().decode("utf-8"))
    except HTTPError as exc:
        body = exc.read().decode("utf-8", errors="replace")
        raise RecoveryCheckError(f"HTTP {exc.code} for {method} {path}: {body}") from exc
    except URLError as exc:
        raise RecoveryCheckError(f"Network error for {method} {path}: {exc}") from exc


def _wait_for_health(timeout_seconds: int = 20) -> None:
    deadline = time.time() + timeout_seconds
    while time.time() < deadline:
        try:
            body = _http_json("GET", "/health")
            if body.get("status") == "ok":
                return
        except RecoveryCheckError:
            time.sleep(0.5)
            continue
        time.sleep(0.2)
    raise RecoveryCheckError("Server did not become healthy in time")


def _launch_server(db_path: Path) -> subprocess.Popen:
    env = os.environ.copy()
    env["APP_DB_PATH"] = str(db_path)
    process = subprocess.Popen(
        [sys.executable, "-m", "uvicorn", "src.main:app", "--host", HOST, "--port", str(PORT)],
        cwd=str(PROJECT_ROOT),
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
        env=env,
    )
    _wait_for_health()
    return process


def _stop_server(process: subprocess.Popen) -> None:
    if process.poll() is not None:
        return
    process.terminate()
    try:
        process.wait(timeout=10)
    except subprocess.TimeoutExpired:
        process.kill()
        process.wait(timeout=5)


def _select_user_without_active_ride(conn: sqlite3.Connection) -> str:
    row = conn.execute(
        """
        SELECT u.user_id
        FROM users u
        WHERE NOT EXISTS (
            SELECT 1
            FROM rides r
            WHERE r.user_id = u.user_id
              AND r.end_time IS NULL
        )
        ORDER BY u.user_id
        LIMIT 1
        """
    ).fetchone()
    if row is None:
        raise RecoveryCheckError("No user available without an active ride")
    return row[0]


def _select_station_with_electric_vehicle(conn: sqlite3.Connection) -> tuple[int, float, float]:
    row = conn.execute(
        """
        SELECT s.station_id, s.lon, s.lat
        FROM stations s
        JOIN vehicles v ON v.station_id = s.station_id
        LEFT JOIN ebikes e ON e.vehicle_id = v.vehicle_id
        LEFT JOIN scooters sc ON sc.vehicle_id = v.vehicle_id
        WHERE v.status = 'available'
          AND (
            (v.vehicle_type = 'electric_bicycle' AND COALESCE(e.battery, 0) >= 28)
            OR
            (v.vehicle_type = 'scooter' AND COALESCE(sc.battery, 0) >= 28)
          )
        ORDER BY CASE v.vehicle_type
            WHEN 'scooter' THEN 1
            WHEN 'electric_bicycle' THEN 2
            ELSE 3
        END, s.station_id
        LIMIT 1
        """
    ).fetchone()
    if row is None:
        raise RecoveryCheckError("No station with an available electric vehicle (battery >= 28) was found")
    return int(row[0]), float(row[1]), float(row[2])


def main() -> None:
    if not DB_PATH.exists():
        raise RecoveryCheckError(f"Database file not found: {DB_PATH}")

    with sqlite3.connect(DB_PATH) as conn:
        user_id = _select_user_without_active_ride(conn)
        station_id, lon, lat = _select_station_with_electric_vehicle(conn)

    server = None
    restarted_server = None
    backup_root = Path(tempfile.mkdtemp(prefix="recovery-check-"))
    temp_db_path = backup_root / "app.db"
    shutil.copy2(DB_PATH, temp_db_path)
    try:
        print("[1/5] Starting API server...")
        server = _launch_server(temp_db_path)

        print("[2/5] Starting and ending a ride to mutate persisted state...")
        ride = _http_json("POST", "/ride/start", {"user_id": user_id, "lon": lon, "lat": lat})
        ride_id = ride["ride_id"]
        end_result = _http_json("POST", "/ride/end", {"ride_id": ride_id, "lon": lon, "lat": lat})
        vehicle_id = end_result["vehicle"]["vehicle_id"]
        expected_battery = end_result["vehicle"].get("battery")
        expected_end_station = end_result["end_station_id"]

        print("[3/5] Simulating server crash/stop...")
        _stop_server(server)
        server = None

        print("[4/5] Restarting API server...")
        restarted_server = _launch_server(temp_db_path)

        print("[5/5] Verifying persisted ride and vehicle state via GET endpoints...")
        recovered_ride = _http_json("GET", f"/ride/{ride_id}")
        recovered_vehicle = _http_json("GET", f"/vehicles/{vehicle_id}")

        if recovered_ride.get("end_time") is None:
            raise RecoveryCheckError("Recovered ride is still active; end_time was not persisted")
        if recovered_ride.get("end_station_id") != expected_end_station:
            raise RecoveryCheckError("Recovered ride has wrong end_station_id")
        if recovered_vehicle.get("status") != end_result["vehicle"].get("status"):
            raise RecoveryCheckError("Recovered vehicle status does not match pre-restart state")
        if recovered_vehicle.get("battery") != expected_battery:
            raise RecoveryCheckError("Recovered vehicle battery does not match pre-restart state")

        print("SUCCESS: Recovery check passed.")
        print(f"Ride persisted: {ride_id}")
        print(f"Vehicle persisted: {vehicle_id} (battery={expected_battery})")
        print(f"End station persisted: {expected_end_station} (started near station {station_id})")
    finally:
        if server is not None:
            _stop_server(server)
        if restarted_server is not None:
            _stop_server(restarted_server)
        shutil.rmtree(backup_root, ignore_errors=True)


if __name__ == "__main__":
    try:
        main()
    except RecoveryCheckError as exc:
        print(f"FAILED: {exc}")
        raise SystemExit(1)
