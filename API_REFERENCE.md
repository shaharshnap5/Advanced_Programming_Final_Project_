# Quick Reference: POST /ride/end API

## API Endpoint

### Basic Request
```bash
curl -X POST http://localhost:8000/ride/end \
  -H "Content-Type: application/json" \
  -d '{
    "ride_id": "RIDE_12345",
    "lon": 34.5,
    "lat": 32.5
  }'
```

---

## Request Format

### Required Fields
| Field | Type | Description | Example |
|-------|------|-------------|---------|
| ride_id | string | Unique ride identifier | "RIDE_ABC123" |
| lon | number | Longitude of drop-off location | 34.5 |
| lat | number | Latitude of drop-off location | 32.5 |

### Validation Rules
- `ride_id`: Non-empty string (required)
- `lon`: Valid float between -180 and 180
- `lat`: Valid float between -90 and 90
- All fields: Must be present in request

---

## Response Format

### Success Response (HTTP 200)
```json
{
  "end_station_id": 1,
  "payment_charged": 15,
  "active_users": ["USER_002", "USER_003", "USER_004"]
}
```

**Response Fields**:
| Field | Type | Description |
|-------|------|-------------|
| end_station_id | integer | ID of station where vehicle was docked |
| payment_charged | integer | Amount charged in ILS (always 15 for normal rides) |
| active_users | array | List of user IDs still in active rides |

---

## Error Responses

### 400 - Bad Request (No Capacity)
```json
{
  "detail": "No station with free capacity available."
}
```
**Causes**:
- All stations are at maximum capacity
- No stations exist in system

---

### 400 - Bad Request (Invalid Data)
```json
{
  "detail": "Missing required fields: ride_id, lon, lat"
}
```
**Causes**:
- ride_id is empty string
- lon or lat is None or missing

---

### 422 - Unprocessable Entity (Validation Error)
```json
{
  "detail": [
    {
      "type": "missing",
      "loc": ["body", "ride_id"],
      "msg": "Field required",
      "input": {}
    }
  ]
}
```
**Causes**:
- Required field missing from JSON
- Incorrect data type (e.g., string instead of number)
- Invalid JSON formatting

---

### 500 - Internal Server Error
```json
{
  "detail": "Internal server error"
}
```
**Causes**:
- Database connection failure
- Unexpected exception in service

---

## Status Codes

| Code | Meaning | Scenario |
|------|---------|----------|
| 200 | OK | Ride successfully ended |
| 400 | Bad Request | Missing required data or no available capacity |
| 422 | Unprocessable Entity | Pydantic validation failed (type mismatch) |
| 500 | Server Error | Unexpected server-side error |

---

## Examples

### Example 1: Successful Ride Completion
```
Request:
POST /ride/end
{
  "ride_id": "RIDE_20250318_001",
  "lon": 34.8,
  "lat": 32.1
}

Response:
200 OK
{
  "end_station_id": 7,
  "payment_charged": 15,
  "active_users": ["USER_ALICE", "USER_BOB"]
}
```

### Example 2: All Stations Full
```
Request:
POST /ride/end
{
  "ride_id": "RIDE_20250318_002",
  "lon": 34.5,
  "lat": 32.5
}

Response:
400 Bad Request
{
  "detail": "No station with free capacity available."
}
```

### Example 3: Missing Field
```
Request:
POST /ride/end
{
  "ride_id": "RIDE_001"
  "lat": 32.5
  ← Missing "lon"
}

Response:
422 Unprocessable Entity
{
  "detail": [
    {
      "type": "missing",
      "loc": ["body", "lon"],
      "msg": "Field required"
    }
  ]
}
```

### Example 4: Invalid Data Type
```
Request:
POST /ride/end
{
  "ride_id": "RIDE_001",
  "lon": "34.5",  ← String instead of number
  "lat": 32.5
}

Response:
422 Unprocessable Entity
{
  "detail": [
    {
      "type": "json_type",
      "loc": ["body", "lon"],
      "msg": "Input should be a valid number, unable to parse string as a number"
    }
  ]
}
```

---

## Implementation Notes

### Station Selection Algorithm
1. Query all stations with current vehicle count
2. Filter stations where `current_count < max_capacity`
3. Calculate Euclidean distance from drop-off location to each station
4. Select station with smallest distance

**Formula**: 
```
distance = sqrt((lon_dropoff - lon_station)² + (lat_dropoff - lat_station)²)
```

### Billing Algorithm
- Fixed price: **15 ILS per ride**
- Future support: 0 ILS for degraded vehicle reports
- Implemented via `Ride.calculate_cost()` method

### Active Users List
- Includes all users with `current_ride_id NOT NULL`
- Excludes user who just completed their ride
- Queried from database on each request
- Sorted by user_id (natural database order)

---

## Testing the Endpoint

### Using Python Requests
```python
import requests
import json

url = "http://localhost:8000/ride/end"
payload = {
    "ride_id": "RIDE_TEST_001",
    "lon": 34.5,
    "lat": 32.5
}

response = requests.post(url, json=payload)
print(f"Status: {response.status_code}")
print(f"Response: {json.dumps(response.json(), indent=2)}")
```

### Using JavaScript/Axios
```javascript
const axios = require('axios');

const config = {
  url: 'http://localhost:8000/ride/end',
  method: 'post',
  data: {
    ride_id: 'RIDE_TEST_001',
    lon: 34.5,
    lat: 32.5
  }
};

axios(config)
  .then(response => console.log(response.data))
  .catch(error => console.error(error.response.data));
```

### Using FastAPI Test Client
```python
from fastapi.testclient import TestClient
from src.main import app

client = TestClient(app)

response = client.post("/ride/end", json={
    "ride_id": "RIDE_TEST_001",
    "lon": 34.5,
    "lat": 32.5
})

assert response.status_code == 200
data = response.json()
print(f"Station: {data['end_station_id']}")
print(f"Payment: {data['payment_charged']} ILS")
print(f"Active Users: {data['active_users']}")
```

---

## Integration Checklist

- [ ] Test endpoint with valid payload
- [ ] Test with missing fields
- [ ] Test with invalid types
- [ ] Test with all stations full
- [ ] Test with no stations
- [ ] Test error handling
- [ ] Test response structure
- [ ] Verify payment calculation
- [ ] Verify active users list
- [ ] Check database updates
- [ ] Verify vehicle docking
- [ ] Test distance calculation

---

## Related Endpoints

- `POST /ride/start` - Start a new ride
- `GET /stations/{id}` - Get station details
- `GET /stations/nearest` - Find nearest station
- `GET /vehicles/{id}` - Get vehicle details
- `GET /users/{id}` - Get user details

---

## Support

For issues or questions:
1. Check test files in `tests/` directory
2. Review `IMPLEMENTATION_SUMMARY.md`
3. See `TECHNICAL_DOCUMENTATION.md` for architecture details
4. Check repository issues on GitHub
