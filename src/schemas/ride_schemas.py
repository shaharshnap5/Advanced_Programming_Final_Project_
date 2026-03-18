from pydantic import BaseModel


class RideStartRequest(BaseModel):
    user_id: str
    lon: float
    lat: float

