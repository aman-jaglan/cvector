"""Pydantic models for asset entities."""

from pydantic import BaseModel, ConfigDict


class AssetResponse(BaseModel):
    """An equipment asset within a facility."""

    id: str
    facility_id: str
    name: str
    type: str
    status: str
    created_at: str

    model_config = ConfigDict(from_attributes=True)
