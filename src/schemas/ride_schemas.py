from pydantic import BaseModel


class RideStartRequest(BaseModel):
    user_id: str
    lon: float
    lat: float

# class RideStartResponse(BaseModel):
#     ride_id: str
#     vehicle_id: str
#     vehicle_type: VehicleType
#     start_station_id: int