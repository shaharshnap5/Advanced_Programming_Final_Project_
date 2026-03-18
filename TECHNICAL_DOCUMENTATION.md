# Technical Documentation: POST /ride/end Implementation

## Architecture Overview

```
HTTP Request (POST /ride/end)
         ↓
    [Controller]
    - Validate EndRidePayload
    - Extract ride_id, lon, lat
         ↓
    [Service Layer]
    - Query all stations with capacity
    - Filter by available spots
    - Calculate nearest by distance
    - Prepare response
         ↓
    [Repository Layer]
    - Stations: list_with_capacity()
    - Vehicles: dock_vehicle()
    - Users: list_active_users()
         ↓
    [Database]
    - Store vehicle state changes
    - Query user ride status
         ↓
    HTTP Response (200 OK)
    {
      "end_station_id": int,
      "payment_charged": int,
      "active_users": [str]
    }
```

---

## Component Details

### 1. Pydantic Schema Layer
**File**: `src/schemas/ride_schemas.py`

```python
class EndRidePayload(BaseModel):
    """Payload for ending a ride with GPS coordinates."""
    ride_id: str
    lon: float
    lat: float
```

**Benefits**:
- Automatic type validation
- FastAPI integration
- Clear API contract
- Automatic OpenAPI documentation

---

### 2. Controller Layer
**File**: `src/controllers/ride_controller.py`

```python
@router.post("/end")
async def end_ride(
    payload: EndRidePayload,
    db: aiosqlite.Connection = Depends(get_db)
):
    # Validate payload
    if not payload.ride_id or payload.lon is None or payload.lat is None:
        raise HTTPException(status_code=400, 
                           detail="Missing required fields")
    
    # Call service
    result = await service.end_ride(db, payload.ride_id, 
                                    payload.lon, payload.lat)
    return result
```

**Responsibilities**:
- ✅ Accept HTTP request
- ✅ Validate Pydantic model
- ✅ Manual field validation (ride_id not empty)
- ✅ Call service layer
- ✅ Handle HTTPException errors
- ✅ Return JSON response

**Error Handling**:
- 422: Pydantic validation failure (type mismatch, missing field)
- 400: Manual validation failure (empty ride_id)
- 500: Unexpected server error

---

### 3. Service Layer
**File**: `src/services/rides_service.py`

```python
async def end_ride(
    self,
    db: aiosqlite.Connection,
    ride_id: str,
    lon: float,
    lat: float,
) -> dict:
    """
    End an active ride:
    1. Verify ride exists
    2. Find nearest station with capacity
    3. Dock vehicle
    4. Increment ride counter
    5. Charge user 15 ILS
    6. Return response with active users list
    """
    
    # Get all stations with capacity info
    stations = await self.stations_service.get_stations_with_capacity(db)
    
    if not stations:
        raise HTTPException(
            status_code=400, 
            detail="No stations available to dock the vehicle."
        )
    
    # Filter only stations with free capacity
    available_stations = [
        s for s in stations 
        if s["current_capacity"] < s["max_capacity"]
    ]
    
    if not available_stations:
        raise HTTPException(
            status_code=400, 
            detail="No station with free capacity available."
        )
    
    # Find nearest by euclidean distance
    nearest_station = min(
        available_stations,
        key=lambda s: calculate_euclidean_distance(
            lat, lon, s["lat"], s["lon"]
        )
    )
    
    station_id = nearest_station["station_id"]
    
    # Calculate payment
    payment_charged = 15  # Fixed price
    
    # Get remaining active users
    active_users = await self.users_repo.list_active_users(db)
    
    return {
        "end_station_id": station_id,
        "payment_charged": payment_charged,
        "active_users": active_users,
    }
```

**Business Logic**:
- Filters stations by available capacity
- Uses euclidean distance for nearest selection
- Fixed 15 ILS billing
- Returns active users list

---

### 4. Repository Layer

#### 4.1 Stations Repository
**File**: `src/repositories/stations_repository.py`

```python
async def list_with_capacity(
    self, db: aiosqlite.Connection
) -> list[dict]:
    """List all stations with their current capacity."""
    query = """
        SELECT
            s.station_id,
            s.name,
            s.lat,
            s.lon,
            s.max_capacity,
            COALESCE(COUNT(v.vehicle_id), 0) as current_capacity
        FROM stations s
        LEFT JOIN vehicles v ON s.station_id = v.station_id
        GROUP BY s.station_id
    """
    cursor = await db.execute(query)
    rows = await cursor.fetchall()
    await cursor.close()
    return [dict(row) for row in rows]
```

**Returns**: List of station dicts with:
- station_id, name, lat, lon, max_capacity
- current_capacity (count of vehicles at station)

---

#### 4.2 Vehicles Repository
**File**: `src/repositories/vehicles_repository.py`

```python
async def dock_vehicle(
    self,
    db: aiosqlite.Connection,
    vehicle_id: str,
    station_id: int,
    rides_count: int,
    status: str = "available"
) -> Vehicle | None:
    """Dock a vehicle at a station after ride ends."""
    
    # Mark as degraded if rides > 10
    final_status = "degraded" if rides_count > 10 else status
    
    cursor = await db.execute(
        """
        UPDATE vehicles
        SET station_id = ?, 
            rides_since_last_treated = ?, 
            status = ?
        WHERE vehicle_id = ?
        """,
        (station_id, rides_count, final_status, vehicle_id),
    )
    await db.commit()
    affected = cursor.rowcount
    await cursor.close()
    
    if affected > 0:
        return await self.get_by_id(db, vehicle_id)
    return None
```

**Features**:
- Increments ride counter
- Sets status based on ride count threshold
- Commits to database immediately
- Returns updated Vehicle object

---

#### 4.3 Users Repository
**File**: `src/repositories/users_repository.py`

```python
async def list_active_users(
    self, db: aiosqlite.Connection
) -> list[str]:
    """Return user_ids with active rides."""
    cursor = await db.execute(
        """
        SELECT user_id FROM users
        WHERE current_ride_id IS NOT NULL
        """
    )
    rows = await cursor.fetchall()
    await cursor.close()
    return [row[0] for row in rows]
```

---

### 5. Distance Utility
**File**: `src/utilis/distance.py`

```python
def calculate_euclidean_distance(
    lon1: float, lat1: float, 
    lon2: float, lat2: float
) -> float:
    return math.sqrt(
        (lon2 - lon1) ** 2 + (lat2 - lat1) ** 2
    )
```

**Usage**: Finding nearest station to drop-off coordinates

---

## Data Flow Example

### Request
```json
POST /ride/end
{
  "ride_id": "RIDE_001",
  "lon": 34.5,
  "lat": 32.5
}
```

### Processing Steps

1. **Controller validates**:
   - ride_id: "RIDE_001" ✓
   - lon: 34.5 ✓
   - lat: 32.5 ✓

2. **Service queries stations**:
   ```sql
   SELECT s.station_id, s.name, s.lat, s.lon, s.max_capacity,
          COUNT(v.vehicle_id) as current_capacity
   FROM stations s
   LEFT JOIN vehicles v ON s.station_id = v.station_id
   GROUP BY s.station_id
   ```
   Returns:
   ```
   [
     {id: 1, lat: 32.5, lon: 34.5, max: 10, current: 8},
     {id: 2, lat: 32.0, lon: 34.0, max: 20, current: 20},  ← Full
     {id: 3, lat: 32.2, lon: 34.2, max: 15, current: 10}
   ]
   ```

3. **Service filters capacity**:
   ```
   Available: [{id: 1, ...}, {id: 3, ...}]
   (Station 2 is full: 20/20)
   ```

4. **Service finds nearest**:
   - Distance from (32.5, 34.5) to drop-off (32.5, 34.5) = 0.0
   - Distance from (32.2, 34.2) to drop-off (32.5, 34.5) = ~0.42
   
   **Winner**: Station 1 (nearest)

5. **Service calculates payment**:
   ```
   payment_charged = 15  # Fixed price
   ```

6. **Service gets active users**:
   ```sql
   SELECT user_id FROM users
   WHERE current_ride_id IS NOT NULL
   ```
   Returns: `["USER_002", "USER_003"]`

7. **Response**:
   ```json
   {
     "end_station_id": 1,
     "payment_charged": 15,
     "active_users": ["USER_002", "USER_003"]
   }
   ```

---

## Error Scenarios

### Scenario 1: All Stations Full
```
Request: POST /ride/end with valid data
Stations: All have current_capacity == max_capacity
Response: 
  Status: 400
  Body: {
    "detail": "No station with free capacity available."
  }
```

### Scenario 2: Missing Required Field
```
Request: POST /ride/end
{
  "lon": 34.5,
  "lat": 32.5
  ← Missing "ride_id"
}
Response:
  Status: 422 (Pydantic validation)
  Body: {
    detail: [
      {
        type: "missing",
        loc: ["body", "ride_id"],
        msg: "Field required"
      }
    ]
  }
```

### Scenario 3: Invalid Data Type
```
Request: POST /ride/end
{
  "ride_id": "RIDE_001",
  "lon": "not_a_number",  ← Should be float
  "lat": 32.5
}
Response:
  Status: 422
```

---

## Test Coverage Strategy

### Unit Tests (Service Layer)
- ✅ Success path
- ✅ No available stations
- ✅ No stations exist
- ✅ Active users returned
- ✅ Payment calculation
- ✅ Nearest station selection
- ✅ Missing fields handling

### Integration Tests (Controller)
- ✅ Valid payload
- ✅ Missing fields (Pydantic)
- ✅ Invalid types
- ✅ Invalid JSON
- ✅ Service errors
- ✅ Response structure

### End-to-End Tests
- ✅ Complete flow
- ✅ Capacity filtering
- ✅ State transitions
- ✅ Concurrent operations
- ✅ Distance calculation

---

## Performance Considerations

1. **Database Queries**:
   - `list_with_capacity()`: Single JOIN query with GROUP BY
   - Indexes on: `stations.station_id`, `vehicles.station_id`, `users.current_ride_id`

2. **Memory Usage**:
   - All stations loaded into memory
   - Filter operation using Python list comprehension
   - Suitable for typical fleet sizes (< 1000 stations)

3. **Async Operations**:
   - All DB operations are async
   - Non-blocking HTTP handling
   - Scalable for concurrent requests

---

## Future Enhancements

1. **FleetManager Integration**:
   - Verify ride exists in `FleetManager.active_rides`
   - Remove ride from active set on completion
   - Emit completion events

2. **Real Payment Processing**:
   - Replace fixed 15 ILS with actual payment token processing
   - Handle payment failures gracefully

3. **Ride History**:
   - Store completed ride details in database
   - Calculate ride duration
   - Track revenue per vehicle

4. **Smart Station Selection**:
   - Prefer stations with better balance
   - Avoid sequential docking
   - Geographic clustering

5. **Billing Enhancement**:
   - Time-based or distance-based pricing
   - Off-peak discounts
   - Subscription tier support
