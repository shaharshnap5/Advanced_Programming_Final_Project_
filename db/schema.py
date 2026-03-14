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

CREATE TABLE IF NOT EXISTS users (
  user_id TEXT PRIMARY KEY,
  payment_token TEXT NOT NULL,
  current_ride_id TEXT
);
"""

