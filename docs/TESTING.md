# Testing

This project uses `pytest` for testing with comprehensive coverage of repositories, services, and controllers.

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

Then open `htmlcov/index.html` in your browser to see detailed coverage.

### Run specific test folder

```bash
pytest tests/repositories
pytest tests/services
pytest tests/controllers
```

### Run specific test file

```bash
pytest tests/repositories/test_stations_repository.py
```

### Run specific test

```bash
pytest tests/repositories/test_stations_repository.py::test_get_by_id
```

### Run with verbose output

```bash
pytest -v
```

### Run and stop on first failure

```bash
pytest -x
```

## Test structure

```
tests/
├── conftest.py           # Test fixtures
├── repositories/         # Repository layer tests
│   ├── test_stations_repository.py
│   └── test_vehicles_repository.py
├── services/            # Service layer tests
│   ├── test_stations_service.py
│   └── test_vehicles_service.py
└── controllers/         # Controller layer tests
    ├── test_stations_controller.py
    └── test_vehicles_controller.py
```

- **Repository tests** ([tests/repositories](tests/repositories))
  - Test database queries with in-memory SQLite
  - Use real `aiosqlite` connections
  - Verify SQL logic and data retrieval

- **Service tests** ([tests/services](tests/services))
  - Test business logic
  - Use mocked repositories
  - Verify service orchestration

- **Controller tests** ([tests/controllers](tests/controllers))
  - Test API endpoints
  - Use mocked services
  - Verify HTTP request/response handling

## Test fixtures

- `test_db` ([tests/conftest.py](tests/conftest.py))
  - Provides an in-memory SQLite database
  - Pre-seeded with test data
  - Isolated per test
    (`tests/repositories/test_<entity>_repository.py`)
  - Test SQL queries with `test_db` fixture

2. **Service tests** (`tests/services/test_<entity>_service.py`)
   - Mock the repository and test business logic
3. **Controller tests** (`tests/controllers/test_<entity>_controller.py`)
   - Tests run automatically on GitHub Actions for:

- Push to `main` or `develop` branches
- Pull requests to `main` or `develop`

The CI pipeline enforces 80% minimum coverage.

## Writing new tests

When adding a new entity:

1. **Repository tests**: Test SQL queries with `test_db` fixture
2. **Service tests**: Mock the repository and test business logic
3. **Controller tests**: Mock the service and test HTTP endpoints

See existing tests as examples.
