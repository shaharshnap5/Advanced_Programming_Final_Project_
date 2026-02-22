# Contributing

## Architecture overview

This project follows a layered structure to keep responsibilities clear:

- **Models**: Pydantic models for request/response and domain data.
- **Repositories**: Low‑level data access (SQL queries, aiosqlite interactions).
- **Services**: Business logic that orchestrates repositories.
- **Controllers**: FastAPI routes; input/output validation and HTTP concerns.

### Where things live

- [src/models](src/models)
  - One file per entity (e.g., [src/models/station.py](src/models/station.py), [src/models/vehicle.py](src/models/vehicle.py)).
  - Define Pydantic models only (no DB code).
- [src/repositories](src/repositories)
  - One file per entity for SQL queries.
  - Only DB access; no HTTP or business logic.
- [src/services](src/services)
  - One file per entity/service.
  - Implements business rules and uses repositories.
- [src/controllers](src/controllers)
  - One file per resource for FastAPI routers.
  - Validate inputs, call services, shape responses.
- [scripts/init_db.py](scripts/init_db.py)
  - Creates tables and seeds the DB.

## Adding a new entity (e.g., users, rides)

1. **Add a model**
   - Create [src/models/<entity>.py](src/models) with a Pydantic model.

2. **Add repository**
   - Create [src/repositories/<entity>\_repository.py](src/repositories).
   - Implement SQL read/write methods.

3. **Add service**
   - Create [src/services/<entity>\_service.py](src/services).
   - Add business logic; call repository methods.

4. **Add controller**
   - Create [src/controllers/<entity>\_controller.py](src/controllers).
   - Add FastAPI routes.

5. **Wire router**
   - Import and include the router in [src/main.py](src/main.py).

## Adding new DB tables (users, rides, etc.)

1. **Update schema**
   - Edit [scripts/init_db.py](scripts/init_db.py) and extend `CREATE_SQL` with the new table(s).

2. **Seed data (optional)**
   - Add CSVs under [data](data) and load them in [scripts/init_db.py](scripts/init_db.py).

3. **Rebuild the DB**
   - Re-run the init script to ensure the DB matches the schema:

```bash
python .\scripts\init_db.py
```

> Note: `init_db.py` uses `CREATE TABLE IF NOT EXISTS` and `INSERT OR IGNORE`. If you change existing tables, delete `data/app.db` first to force a clean rebuild.

## Keeping the DB up to date

- After schema or seed changes, run:

```bash
python .\scripts\init_db.py
```

- If you need a clean rebuild:
  1. Delete `data/app.db`
  2. Run the script again

## Quick dev loop

```bash
python .\scripts\init_db.py
uvicorn src.main:app --reload
```
