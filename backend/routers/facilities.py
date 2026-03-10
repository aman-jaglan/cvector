"""Facility endpoints — list all facilities or get one with its assets."""

import aiosqlite
from fastapi import APIRouter, Depends, HTTPException

from backend.dependencies import get_db
from backend.models.asset import AssetResponse
from backend.models.facility import FacilityDetailResponse, FacilityResponse

router = APIRouter(prefix="/api/facilities", tags=["facilities"])


@router.get("/", response_model=list[FacilityResponse])
async def list_facilities(db: aiosqlite.Connection = Depends(get_db)):
    """List all facilities in the system.

    Returns basic facility information without nested assets.
    Use the detail endpoint to include asset data.
    """
    async with db.execute(
        "SELECT id, name, type, location, status, created_at FROM facilities ORDER BY name"
    ) as cursor:
        rows = await cursor.fetchall()
        return [dict(row) for row in rows]


@router.get("/{facility_id}", response_model=FacilityDetailResponse)
async def get_facility(facility_id: str, db: aiosqlite.Connection = Depends(get_db)):
    """Get a single facility with all of its assets.

    Returns full facility details including the list of equipment
    assets that belong to it.
    """
    async with db.execute(
        "SELECT id, name, type, location, status, created_at FROM facilities WHERE id = ?",
        (facility_id,),
    ) as cursor:
        facility_row = await cursor.fetchone()

    if not facility_row:
        raise HTTPException(status_code=404, detail="Facility not found")

    async with db.execute(
        "SELECT id, facility_id, name, type, status, created_at FROM assets WHERE facility_id = ? ORDER BY name",
        (facility_id,),
    ) as cursor:
        asset_rows = await cursor.fetchall()

    facility = dict(facility_row)
    facility["assets"] = [dict(row) for row in asset_rows]
    return facility
