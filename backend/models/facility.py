"""Pydantic models for facility entities."""

from pydantic import BaseModel, ConfigDict

from backend.models.asset import AssetResponse


class FacilityResponse(BaseModel):
    """A facility without its nested assets."""

    id: str
    name: str
    type: str
    location: str
    status: str
    created_at: str

    model_config = ConfigDict(from_attributes=True)


class FacilityDetailResponse(FacilityResponse):
    """A facility with its list of assets included."""

    assets: list[AssetResponse]
