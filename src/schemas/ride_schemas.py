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

