"""Pydantic models for sensor reading entities."""

from pydantic import BaseModel, ConfigDict


class SensorReadingResponse(BaseModel):
    """A single sensor reading from an asset."""

    id: int
    asset_id: str
    facility_id: str
    metric_name: str
    value: float
    unit: str
    recorded_at: str

    model_config = ConfigDict(from_attributes=True)
