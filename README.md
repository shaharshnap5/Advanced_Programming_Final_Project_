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

`python .\scripts\init_db.py`

See [docs/DB_SETUP.md](docs/DB_SETUP.md) for full details.

### 3) Run the server

`uvicorn src.main:app --reload`

Open http://127.0.0.1:8000 in your browser.

## Documentation

- [docs/DB_SETUP.md](docs/DB_SETUP.md)
- [docs/CONTRIBUTING.md](docs/CONTRIBUTING.md)
