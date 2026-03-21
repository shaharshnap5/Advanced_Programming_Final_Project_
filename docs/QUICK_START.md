# Quick Start

This guide gets the project running locally in a few minutes.

## Prerequisites

- Python 3.11+ (tested on 3.11 and 3.12)
- `pip`
- Git (optional)

## 1) Clone and enter the project

```bash
git clone <your-repo-url>
cd Advanced_Programming_Final_Project_
```

## 2) Create a virtual environment

```bash
python -m venv .venv
```

Activate it:

Windows (PowerShell):

```bash
.\.venv\Scripts\Activate.ps1
```

macOS/Linux:

```bash
source .venv/bin/activate
```

## 3) Install dependencies

```bash
pip install -r requirements.txt
```

## 4) Initialize the database

```bash
python ./scripts/init_db.py
```

For a clean rebuild:

```bash
python ./scripts/init_db.py --reset-db
```

## 5) Run the API server

```bash
uvicorn src.main:app --reload
```

Server URL: `http://127.0.0.1:8000`

## 6) Verify the server

Open in browser:

- `http://127.0.0.1:8000/`
- `http://127.0.0.1:8000/health`

## 7) Run tests

```bash
pytest
```

With coverage:

```bash
pytest --cov=src --cov-report=term-missing
```

## 8) API testing (Postman)

Import:

- [docs/postman_collection.json](postman_collection.json)

Set `baseUrl` to:

- `http://127.0.0.1:8000`

## Troubleshooting

- If DB looks out of sync, run reset:
  - `python ./scripts/init_db.py --reset-db`
- If dependencies fail, ensure the virtual environment is activated.
- If port is busy, run uvicorn on another port:
  - `uvicorn src.main:app --reload --port 8001`
