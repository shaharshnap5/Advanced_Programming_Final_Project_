from pydantic import BaseModel, model_validator
from src.models.vehicle import Vehicle


class RideStartRequest(BaseModel):
    user_id: str
    lon: float | None = None
    lat: float | None = None
    vehicle_id: str | None = None

    @model_validator(mode="after")
    def validate_location_or_vehicle(self) -> "RideStartRequest":
        has_vehicle = self.vehicle_id is not None and self.vehicle_id != ""
        has_coordinates = self.lon is not None and self.lat is not None

        if not has_vehicle and not has_coordinates:
            raise ValueError("Provide either vehicle_id or both lon and lat")

        if self.vehicle_id is not None and self.vehicle_id == "":
            raise ValueError("vehicle_id cannot be empty")

        return self


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

