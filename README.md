# advanced-programing-final-project

## Quickstart

### 1) Create and activate a virtual environment

Windows (PowerShell):

1. `python -m venv .venv`
2. `.\.venv\Scripts\Activate.ps1`

macOS/Linux (bash/zsh):

1. `python -m venv .venv`
2. `source .venv/bin/activate`

### 2) Install dependencies

`pip install -r requirements.txt`

### 2.5) Initialize the database

Windows (PowerShell):

`python .\scripts\init_db.py`

macOS/Linux (bash/zsh):

`python ./scripts/init_db.py`
Reset the database (drop all tables and recreate):

`python .\scripts\init_db.py --reset-db`

See [docs/DB_SETUP.md](docs/DB_SETUP.md) for full details.

### 3) Run the server

`uvicorn src.main:app --reload`

Open http://127.0.0.1:8000 in your browser.

## Testing

Run tests:

```bash
pytest
```

Run with coverage:

```bash
pytest --cov=src --cov-report=term-missing
```

See [docs/TESTING.md](docs/TESTING.md) for full details.

## Documentation

- [docs/DB_SETUP.md](docs/DB_SETUP.md)
- [docs/CONTRIBUTING.md](docs/CONTRIBUTING.md)
- [docs/TESTING.md](docs/TESTING.md)

## Persistence & Recovery Strategy

This project uses SQLite as the single source of truth for runtime state.

- Runtime database file: `data/app.db`
- Connection library: `aiosqlite` (see `src/db.py`)
- Durability settings per request:
	- `PRAGMA journal_mode=WAL;`
	- `PRAGMA synchronous=FULL;`
	- `PRAGMA foreign_keys=ON;`

### Initialization vs Runtime State

- CSV files under `data/*.csv` are bootstrap inputs only.
- `python scripts/init_db.py` loads CSV data into SQLite.
- After startup, all state changes (rides, vehicle status, battery values) are persisted only in `data/app.db`.
- Restarting Uvicorn does not reset state unless `--reset-db` is explicitly used in the init script.

### Transaction Integrity

- FastAPI request scope uses `get_db()` to enforce commit/rollback semantics.
- Multi-step flows (for example, ride start and ride end) are executed atomically in the service layer:
	- begin transaction
	- perform all related repository writes
	- commit only if all writes succeed
	- rollback on any exception
- This prevents partial updates (for example, vehicle rented but ride row missing) during failures.

### Verified Recovery (Crash/Restart QA)

Run the automated recovery check:

```bash
python scripts/verify_recovery.py
```

The script performs this sequence:

1. Starts the API server on a temporary port.
2. Starts and ends a ride (to mutate vehicle + ride persisted state).
3. Stops the server (simulated crash/stop).
4. Restarts the server.
5. Verifies with GET endpoints that ride completion and vehicle battery/state were preserved.
