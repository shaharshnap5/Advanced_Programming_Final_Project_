from __future__ import annotations

import asyncio
import sys
from pathlib import Path

import pandas as pd

PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT))

from src.db import get_db
STATIONS_CSV = PROJECT_ROOT / "data" / "stations.csv"
VEHICLES_CSV = PROJECT_ROOT / "data" / "vehicles.csv"

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
"""


async def init_db() -> None:
    async with get_db() as db:
        await db.executescript(CREATE_SQL)

        stations = pd.read_csv(STATIONS_CSV)
        await db.executemany(
            "INSERT OR IGNORE INTO stations(station_id,name,lat,lon,max_capacity) VALUES(?,?,?,?,?)",
            stations[["station_id", "name", "lat", "lon", "max_capacity"]].itertuples(
                index=False, name=None
            ),
        )

        vehicles = pd.read_csv(VEHICLES_CSV)
        await db.executemany(
            """INSERT OR IGNORE INTO vehicles(
                   vehicle_id, station_id, vehicle_type, status, rides_since_last_treated, last_treated_date
               ) VALUES(?,?,?,?,?,?)""",
            vehicles[[
                "vehicle_id",
                "station_id",
                "vehicle_type",
                "status",
                "rides_since_last_treated",
                "last_treated_date",
            ]].itertuples(index=False, name=None),
        )


if __name__ == "__main__":
    asyncio.run(init_db())
    print("DB initialized")
