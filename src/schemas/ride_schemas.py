from pydantic import BaseModel, Field


class RideStartRequest(BaseModel):
    user_id: str = Field(..., min_length=1, description="User ID starting the ride")
    lon: float = Field(..., ge=-180, le=180, description="Longitude coordinate")
    lat: float = Field(..., ge=-90, le=90, description="Latitude coordinate")


class RideEndRequest(BaseModel):
    user_id: str = Field(..., min_length=1, description="User ID ending the ride")
    lon: float = Field(..., ge=-180, le=180, description="Longitude coordinate")
    lat: float = Field(..., ge=-90, le=90, description="Latitude coordinate")
    is_degraded: bool = Field(default=False, description="Whether vehicle is degraded")

