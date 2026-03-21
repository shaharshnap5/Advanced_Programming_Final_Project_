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
- [docs/postman_collection.json](docs/postman_collection.json)
