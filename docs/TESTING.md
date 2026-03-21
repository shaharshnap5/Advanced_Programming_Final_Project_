# Testing

This project uses `pytest` for unit, integration, and API/controller testing.

## Running tests

### Run all tests

```bash
pytest
```

### Run with coverage

```bash
pytest --cov=src --cov-report=term-missing
```

### Run with HTML coverage report

```bash
pytest --cov=src --cov-report=html
```

Then open `htmlcov/index.html`.

### Run specific folders

```bash
pytest tests/models
pytest tests/repositories
pytest tests/services
pytest tests/controllers
```

### Run a specific file / test

```bash
pytest tests/controllers/test_rides_controller.py
pytest tests/controllers/test_rides_controller.py::test_get_active_users_via_api
```

### Useful flags

```bash
pytest -v      # verbose
pytest -x      # stop on first failure
```

## Test structure

```text
tests/
  conftest.py
  controllers/
  models/
  repositories/
  services/
  test_ride_integration.py
  test_rides_csv_data.py
```

- **Model tests**: domain/entity behavior and invariants
- **Repository tests**: SQL queries and persistence semantics
- **Service tests**: business rules and orchestration
- **Controller tests**: endpoint status codes, payloads, response contracts
- **Integration tests**: end-to-end ride and data workflows

## Fixtures

Shared fixtures are defined in [tests/conftest.py](../tests/conftest.py), including database setup helpers used across layers.

## CI

GitHub Actions runs tests on pushes and pull requests to `main`.

- Python versions: 3.11 and 3.12
- Coverage gate: `--cov-fail-under=80`

See workflow: [.github/workflows/ci.yml](../.github/workflows/ci.yml)

## API testing with Postman

For manual API checks, use:

- [docs/postman_collection.json](postman_collection.json)

Import it into Postman and set `baseUrl` (default `http://127.0.0.1:8000`).

## Adding new tests

When adding a new feature/entity, include:

1. Repository test(s)
2. Service test(s)
3. Controller/API test(s)
4. Integration test when behavior spans layers
