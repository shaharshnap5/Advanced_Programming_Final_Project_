from __future__ import annotations

import asyncio
import sys
from pathlib import Path

import pandas as pd
import aiosqlite


PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT))

#from src.db import get_db
from db.schema import CREATE_SQL

STATIONS_CSV = PROJECT_ROOT / "data" / "stations.csv"
VEHICLES_CSV = PROJECT_ROOT / "data" / "vehicles.csv"
DB_PATH = PROJECT_ROOT / "data" / "app.db"


# async def init_db() -> None:
#     async with get_db() as db:
#         await db.executescript(CREATE_SQL)
#
#         stations = pd.read_csv(STATIONS_CSV)
#         await db.executemany(
#             "INSERT OR IGNORE INTO stations(station_id,name,lat,lon,max_capacity) VALUES(?,?,?,?,?)",
#             stations[["station_id", "name", "lat", "lon", "max_capacity"]].itertuples(
#                 index=False, name=None
#             ),
#         )
#
#         vehicles = pd.read_csv(VEHICLES_CSV)
#         await db.executemany(
#             """INSERT OR IGNORE INTO vehicles(
#                    vehicle_id, station_id, vehicle_type, status, rides_since_last_treated, last_treated_date
#                ) VALUES(?,?,?,?,?,?)""",
#             vehicles[[
#                 "vehicle_id",
#                 "station_id",
#                 "vehicle_type",
#                 "status",
#                 "rides_since_last_treated",
#                 "last_treated_date",
#             ]].itertuples(index=False, name=None),
#         )

async def init_db() -> None:
    # 2. Connect directly to the database file instead of using get_db()
    async with aiosqlite.connect(DB_PATH) as db:
        print("Creating tables...")
        await db.executescript(CREATE_SQL)

        print("Loading stations...")
        stations = pd.read_csv(STATIONS_CSV)
        await db.executemany(
            "INSERT OR IGNORE INTO stations(station_id,name,lat,lon,max_capacity) VALUES(?,?,?,?,?)",
            stations[["station_id", "name", "lat", "lon", "max_capacity"]].itertuples(
                index=False, name=None
            ),
        )

        print("Loading vehicles...")
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
        print("Creating test user...")
        await db.execute(
            "INSERT OR IGNORE INTO users (user_id, payment_token) VALUES (?, ?)",
            ("test_user_001", "tok_visa_1234")
        )
        # -------------------------------------

        # 3. Commit the changes so they permanently save to the file!
        await db.commit()


if __name__ == "__main__":
    asyncio.run(init_db())
    print("DB initialized")
