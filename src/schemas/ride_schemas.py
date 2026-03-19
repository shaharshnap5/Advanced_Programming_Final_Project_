from pydantic import BaseModel


class RideStartRequest(BaseModel):
    user_id: str
    lon: float
    lat: float


class EndRidePayload(BaseModel):
    """Payload for ending a ride with GPS coordinates of the drop-off location."""
    ride_id: str
    lon: float
    lat: float

