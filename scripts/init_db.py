from __future__ import annotations

import asyncio
import argparse
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
USERS_CSV = PROJECT_ROOT / "data" / "users.csv"
DB_PATH = PROJECT_ROOT / "data" / "app.db"

async def init_db(reset_db: bool = False) -> None:
    # 2. Connect directly to the database file instead of using get_db()
    async with aiosqlite.connect(DB_PATH) as db:
        if reset_db:
            print("Resetting and creating tables...")
            await db.executescript(
                """
                DROP TABLE IF EXISTS rides;
                DROP TABLE IF EXISTS users;
                DROP TABLE IF EXISTS vehicles;
                DROP TABLE IF EXISTS stations;
                """
            )
        else:
            print("Creating tables (without reset)...")
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
        print("Loading users...")
        users = pd.read_csv(USERS_CSV)
        await db.executemany(
            """INSERT OR IGNORE INTO users(
                   user_id, first_name, last_name, email, payment_token
               ) VALUES(?,?,?,?,?)""",
            users[["user_id", "first_name", "last_name", "email", "payment_token"]].itertuples(
                index=False, name=None
            ),
        )
        # -------------------------------------

        # 3. Commit the changes so they permanently save to the file!
        await db.commit()


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Initialize and seed the SQLite database.")
    parser.add_argument(
        "--reset-db",
        action="store_true",
        help="Drop all tables before creating and seeding them.",
    )
    args = parser.parse_args()

    asyncio.run(init_db(reset_db=args.reset_db))
    print("DB initialized")
