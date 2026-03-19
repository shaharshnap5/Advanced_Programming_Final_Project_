from pydantic import BaseModel, Field


class VehicleReportDegradedRequest(BaseModel):
    """Request body for reporting a vehicle as degraded."""
    pass  # No body needed, vehicle_id comes from path parameter
