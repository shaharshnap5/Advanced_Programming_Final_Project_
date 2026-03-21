# Database setup

> **Note**: CSV datasets under `data/` are part of the project. The SQLite file `data/app.db` is generated locally when you run the init script.

## 1) Install dependencies

```bash
pip install -r requirements.txt
```

## 2) Initialize the SQLite database

```bash
python ./scripts/init_db.py
```

This creates missing tables and seeds data from CSV files:

- `data/stations.csv`
- `data/vehicles.csv`
- `data/users.csv`
- `data/rides.csv`

To fully reset the database (drop all tables and recreate):

```bash
python ./scripts/init_db.py --reset-db
```

You should now have data/app.db.

## 3) Run the API

```bash
uvicorn src.main:app --reload
```

Example request:

```bash
curl "http://127.0.0.1:8000/stations/nearest?lon=34.78&lat=32.08"
```

## 4) Query the database interactively

To run SQL queries directly against the database from the terminal:

```bash
python ./scripts/query_shell.py
```

You'll get an interactive shell prompt:

```
SQLite interactive shell. Type 'exit' or 'quit' to exit.

sqlite> SELECT * FROM stations LIMIT 3
{'station_id': 1, 'name': 'Station_0001', 'lat': 32.058323, 'lon': 34.815431, 'max_capacity': 21}
...

sqlite> SELECT * FROM vehicles WHERE station_id = 1
...

sqlite> exit
Goodbye!
```

You can run any SQL query (SELECT, INSERT, UPDATE, DELETE) until you type `exit` or `quit`.
