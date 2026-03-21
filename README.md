# Shared Mobility Fleet Backend

Python 3.12 async REST backend for a shared mobility fleet simulation.

---

## 1) Project Overview

This project implements a backend service for managing a shared mobility system (bicycles, e-bikes, and scooters). The API supports core operations for:

- users
- vehicles
- stations
- rides
- maintenance workflows

The server is built as an **async REST API** (FastAPI + `aiosqlite`) to support non-blocking I/O and predictable behavior under concurrent requests.

This is a **simulation-oriented system** designed for academic evaluation:

- realistic fleet rules (availability, degradation, treatment)
- deterministic business logic
- persistent state in SQLite
- reproducible data loading from CSV datasets

---

## 2) Features

- User registration / login-by-id flow
- Start ride and end ride flows
- Vehicle degradation reporting
- Vehicle maintenance (treat + recover)
- Nearest station lookup by coordinates
- Active users in rides tracking
- Async API endpoints (non-blocking DB operations)
- State persistence via SQLite
- Structured validation and HTTP error handling

---

## 3) Architecture Overview

The system follows a layered architecture with clear separation of concerns.

- **Domain layer**: entity models and domain behavior
- **Service layer**: use-cases and business rules
- **Repository layer**: SQL/data access abstraction
- **API layer**: HTTP routes, request/response contracts

### Patterns Used

- **Repository Pattern** for DB access encapsulation
- **Factory Pattern** for polymorphic vehicle instantiation
- **Service Layer Pattern** for business orchestration

### ASCII Architecture Diagram

```text
Clients (Postman / tests / browser)
								|
								v
				+------------------+
				|   API Layer      |
				| FastAPI routers  |
				+------------------+
								|
								v
				+------------------+
				| Service Layer    |
				| Business rules   |
				+------------------+
								|
								v
				+------------------+
				| Repository Layer |
				| SQL + persistence|
				+------------------+
								|
								v
				+------------------+
				| SQLite (app.db)  |
				+------------------+

Domain models are shared across API/Service/Repository boundaries.
```

---

## 4) Domain Model

### User

- Identity and profile data
- Payment token (simulated billing token)
- Can start rides if no conflicting active ride

### Vehicle

- Base `Vehicle` + subtypes (`Bicycle`, `ElectricBicycle`, `Scooter`)
- Electric vehicles enforce battery constraints
- Lifecycle methods: rent, return, report degraded, treat

### Station

- Geolocation (`lat`, `lon`)
- Capacity-limited docking inventory
- Used for nearest-station and docking decisions

### Ride

- Links user ↔ vehicle ↔ start/end stations
- Tracks start/end timestamps
- Tracks degraded ride outcomes

### Maintenance

- Triggered by degradation report or treatment thresholds
- Treatment resets counters and restores availability

### Vehicle States

- **docked/available**: can be rented if constraints pass
- **active ride/rented**: currently in use
- **degraded**: blocked until treated

### Ride Lifecycle

1. User starts ride near location
2. System selects eligible vehicle
3. Vehicle status changes to rented
4. User ends ride near destination
5. Vehicle docks at nearest station with free capacity
6. Counters/payment/degradation logic is applied

---

## 5) State Management

The backend actively manages dynamic operational state:

- **active rides**: rides with `end_time IS NULL`
- **station inventory**: current docked vehicles per station
- **degraded vehicles**: excluded from normal rental flow
- **active users**: derived from currently active rides
- **concurrency handling**: async locks are used in critical flows (e.g., user active ride checks) to reduce race conditions

---

## 6) Persistence Model

Data is stored in SQLite (`data/app.db`) and survives server restarts.

### Persists Across Restarts

- users
- vehicles (including status and maintenance counters)
- stations
- rides (historical + active)

### Dataset Loading

- CSV files in [data](data) are loaded by [scripts/init_db.py](scripts/init_db.py)
- Can initialize or fully reset/rebuild state

### Limitations

- SQLite is single-node, file-based persistence
- No distributed transactions or multi-node coordination
- No real payment provider integration (simulated)

---

## 7) Dataset

### Required Files

- [data/stations.csv](data/stations.csv)
- [data/vehicles.csv](data/vehicles.csv)
- [data/users.csv](data/users.csv)
- [data/rides.csv](data/rides.csv)

### Expected Structure

```text
data/
	stations.csv
	vehicles.csv
	users.csv
	rides.csv
	app.db                # generated locally
```

### CSV Format

- Header row is required
- IDs are expected to follow seeded patterns:
  - `USER001`, `USER002`, ...
  - `V000001`, `V000002`, ...
  - `RIDE001`, `RIDE002`, ...
  - `station_id` as integer

### Loading Process

Run:

```bash
python ./scripts/init_db.py
```

Reset and rebuild:

```bash
python ./scripts/init_db.py --reset-db
```

---

## 8) API Documentation

### Base URL

```text
http://127.0.0.1:8000
```

### Route Naming Note

The assignment endpoint names are listed below as requested.
Current implementation uses pluralized prefixes (`/users`, `/rides`, `/vehicles`, `/stations`).

### Endpoints List

- `POST /register` (implemented as `POST /users/register`)
- `POST /ride/start` (implemented as `POST /rides/start`)
- `POST /ride/end` (implemented as `POST /rides/end`)
- `POST /vehicle/treat` (implemented as `POST /vehicles/{vehicle_id}/treat`)
- `POST /vehicle/report-degraded` (implemented as `POST /vehicles/{vehicle_id}/report-degraded`)
- `GET /stations/nearest`
- `GET /rides/active-users`

### Request / Response Examples

#### 1) Register User

```http
POST /users/register
Content-Type: application/json

{
	"user_id": "USER011",
	"first_name": "Dana",
	"last_name": "Levi",
	"email": "dana.levi@example.com"
}
```

```json
{
  "message": "User created successfully",
  "user": {
    "user_id": "USER011",
    "first_name": "Dana",
    "last_name": "Levi",
    "email": "dana.levi@example.com",
    "payment_token": "<generated_token>"
  }
}
```

#### 2) Start Ride

```http
POST /rides/start
Content-Type: application/json

{
	"user_id": "USER001",
	"lon": 34.7818,
	"lat": 32.0853
}
```

```json
{
  "ride_id": "<uuid>",
  "user_id": "USER001",
  "vehicle_id": "V000123",
  "start_station_id": 45,
  "start_time": "2026-03-21T12:34:56"
}
```

#### 3) End Ride

```http
POST /rides/end
Content-Type: application/json

{
	"ride_id": "<ride_id>",
	"lon": 34.7900,
	"lat": 32.0900
}
```

```json
{
  "end_station_id": 50,
  "payment_charged": 15,
  "vehicle": {
    "vehicle_id": "V000123",
    "station_id": 50,
    "vehicle_type": "electric_bicycle",
    "status": "available",
    "rides_since_last_treated": 4,
    "last_treated_date": null,
    "battery": 86
  }
}
```

#### 4) Treat Vehicle

```http
POST /vehicles/V000123/treat?station_id=10
```

```json
{
  "vehicle_id": "V000123",
  "status": "available",
  "rides_since_last_treated": 0
}
```

#### 5) Report Vehicle Degraded

```http
POST /vehicles/V000123/report-degraded
```

```json
{
  "vehicle_id": "V000123",
  "status": "degraded"
}
```

#### 6) Nearest Station

```http
GET /stations/nearest?lon=34.78&lat=32.08
```

```json
{
  "station_id": 63,
  "name": "Station_0063",
  "lat": 32.085618,
  "lon": 34.805101,
  "distance": 0.02
}
```

#### 7) Active Users

```http
GET /rides/active-users
```

```json
[
  {
    "user_id": "USER001",
    "first_name": "Noam",
    "last_name": "Levi",
    "email": "noam.levi@example.com",
    "payment_token": "tok_mock_001"
  }
]
```

### Error Codes

- `200` OK
- `201` Created
- `400` Bad Request (validation/business rule violation)
- `404` Not Found
- `409` Conflict
- `422` Unprocessable Entity (schema validation)
- `500` Internal Server Error

Postman collection: [docs/postman_collection.json](docs/postman_collection.json)

---

## 9) Project Structure

### Conceptual Layered Structure

```text
src/
	domain/         # domain entities and business objects
	services/       # use-case orchestration
	repositories/   # persistence access
	api/            # route handlers/controllers
tests/
data/
docs/
```

### Current Repository Structure

```text
src/
	controllers/
	models/
	repositories/
	services/
	schemas/
tests/
data/
docs/
scripts/
```

---

## 10) Quick Start

For a streamlined setup guide, see [docs/QUICK_START.md](docs/QUICK_START.md).

### Requirements

- Python 3.12
- pip

### Install

```bash
python -m venv .venv
```

Windows:

```bash
.\.venv\Scripts\Activate.ps1
```

macOS/Linux:

```bash
source .venv/bin/activate
```

Install dependencies:

```bash
pip install -r requirements.txt
```

Initialize DB:

```bash
python ./scripts/init_db.py
```

Run server:

```bash
uvicorn src.main:app --reload
```

Run tests:

```bash
pytest
```

---

## 11) Testing

Test suite includes:

- **Unit tests** for model and service logic
- **Integration tests** for repository/database flows
- **API/controller tests** for endpoint behavior

Coverage target:

- minimum 80% expected in CI/class rubric

Useful commands:

```bash
pytest
pytest --cov=src --cov-report=term-missing
pytest tests/controllers
pytest tests/services
pytest tests/repositories
```

Reference: [docs/TESTING.md](docs/TESTING.md)

---

## 12) Development Workflow

Recommended team workflow:

1. Create a feature branch per task (`feature/<short-name>`)
2. Keep commits focused and atomic
3. Open PR with clear summary + test evidence
4. Require at least one review before merge
5. Merge only after tests pass

PR expectations:

- linked requirement/task
- updated tests
- no regression in existing behavior
- clean, readable code and doc updates when needed

---

## 13) Error Handling

The API uses explicit HTTP semantics and validation:

- FastAPI/Pydantic request validation for schema and types
- Service-level rule checks translated to HTTP errors
- Global handlers for unknown routes and unexpected failures

Typical behavior:

- Invalid payload format: `400` / `422`
- Missing resources: `404`
- Business conflict (e.g., duplicate active ride): `409`
- Unexpected exceptions: `500`

---

## 14) Design Decisions

### Deterministic Vehicle Selection

Vehicle assignment uses deterministic ordering by type priority and ID for reproducibility and predictable tests.

### Degradation Rules

- Manual report can mark vehicle degraded immediately
- Maintenance counters drive treatment eligibility
- Treated vehicles reset counters and become available

### Pricing Logic

Current simulation uses fixed ride charge for normal completions (e.g., 15 ILS), with behavior designed to be extensible for richer pricing strategies.

---

## 15) Future Improvements

- Authentication and authorization (JWT/roles)
- Real payment gateway integration
- Dynamic pricing (time, distance, vehicle type)
- Better observability (structured logs, tracing, metrics)
- Containerization and production deployment profile
- Background workers for maintenance scheduling
- OpenAPI examples + SDK generation

---

## Additional Documentation

- [docs/QUICK_START.md](docs/QUICK_START.md)
- [docs/DB_SETUP.md](docs/DB_SETUP.md)
- [docs/CONTRIBUTING.md](docs/CONTRIBUTING.md)
- [docs/TESTING.md](docs/TESTING.md)
- [docs/LINTING.md](docs/LINTING.md)
- [docs/postman_collection.json](docs/postman_collection.json)
