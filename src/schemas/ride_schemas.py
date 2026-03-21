from pydantic import BaseModel
from src.models.vehicle import Vehicle


class RideStartRequest(BaseModel):
    user_id: str
    lon: float | None = None
    lat: float | None = None


class ActiveUsersResponse(BaseModel):
    active_user_ids: list[str]


class EndRidePayload(BaseModel):
    """Payload for ending a ride with GPS coordinates of the drop-off location."""

    ride_id: str
    lon: float
    lat: float


class EndRideResponse(BaseModel):
    end_station_id: int
    payment_charged: int
    vehicle: Vehicle
