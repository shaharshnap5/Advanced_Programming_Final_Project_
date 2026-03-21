"""Database schema definition."""

CREATE_SQL = """
CREATE TABLE IF NOT EXISTS stations (
  station_id INTEGER PRIMARY KEY,
  name TEXT NOT NULL,
  lat REAL NOT NULL,
  lon REAL NOT NULL,
  max_capacity INTEGER NOT NULL
);

CREATE TABLE IF NOT EXISTS vehicles (
  vehicle_id TEXT PRIMARY KEY,
  station_id INTEGER,
  vehicle_type TEXT NOT NULL,
  status TEXT NOT NULL,
  rides_since_last_treated INTEGER NOT NULL,
  last_treated_date TEXT,
  FOREIGN KEY(station_id) REFERENCES stations(station_id)
);

CREATE TABLE IF NOT EXISTS electric_bicycles (
  vehicle_id TEXT PRIMARY KEY,
  battery INTEGER NOT NULL DEFAULT 100,
  FOREIGN KEY(vehicle_id) REFERENCES vehicles(vehicle_id) ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS scooters (
  vehicle_id TEXT PRIMARY KEY,
  battery INTEGER NOT NULL DEFAULT 100,
  FOREIGN KEY(vehicle_id) REFERENCES vehicles(vehicle_id) ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS users (
  user_id TEXT PRIMARY KEY,
  first_name TEXT NOT NULL,
  last_name TEXT NOT NULL,
  email TEXT NOT NULL,
  payment_token TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS rides (
    ride_id TEXT PRIMARY KEY,
    user_id TEXT NOT NULL,
    vehicle_id TEXT NOT NULL,
    start_station_id INTEGER NOT NULL,
    end_station_id INTEGER,
    is_degraded_report BOOLEAN DEFAULT 0,
    start_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    end_time TIMESTAMP,
    FOREIGN KEY(user_id) REFERENCES users(user_id),
    FOREIGN KEY(vehicle_id) REFERENCES vehicles(vehicle_id),
    FOREIGN KEY(start_station_id) REFERENCES stations(station_id),
    FOREIGN KEY(end_station_id) REFERENCES stations(station_id)
);
"""

