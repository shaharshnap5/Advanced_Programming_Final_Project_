from pydantic import BaseModel


class RideStartRequest(BaseModel):
    user_id: str
    lon: float
    lat: float


class ActiveUsersResponse(BaseModel):
    active_user_ids: list[str]
class EndRidePayload(BaseModel):
    """Payload for ending a ride with GPS coordinates of the drop-off location."""
    ride_id: str
    lon: float
    lat: float


class EndRideResponse(BaseModel):
    """Response after ending a ride."""
    end_station_id: int
    payment_charged: int
    active_users: list[str]

