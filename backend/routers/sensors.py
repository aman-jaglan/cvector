"""Sensor reading endpoints — query time-series data with flexible filters."""

from typing import Optional

import aiosqlite
from fastapi import APIRouter, Depends, Query

from backend.dependencies import get_db
from backend.models.sensor import SensorReadingResponse

router = APIRouter(prefix="/api/sensors", tags=["sensors"])


@router.get("/readings", response_model=list[SensorReadingResponse])
async def get_sensor_readings(
    facility_id: Optional[str] = Query(None, description="Filter by facility ID"),
    asset_id: Optional[str] = Query(None, description="Filter by asset ID"),
    metric_name: Optional[str] = Query(None, description="Filter by metric name (temperature, pressure, power_consumption, production_output)"),
    start_time: Optional[str] = Query(None, description="Start of time range (ISO 8601 format)"),
    end_time: Optional[str] = Query(None, description="End of time range (ISO 8601 format)"),
    limit: int = Query(1000, ge=1, le=10000, description="Maximum number of readings to return"),
    db: aiosqlite.Connection = Depends(get_db),
):
    """Query sensor readings with optional filters.

    All filters are optional and can be combined. Results are ordered
    by recorded_at descending (most recent first) and capped by the
    limit parameter.
    """
    query = "SELECT id, asset_id, facility_id, metric_name, value, unit, recorded_at FROM sensor_readings WHERE 1=1"
    params: list = []

    if facility_id:
        query += " AND facility_id = ?"
        params.append(facility_id)

    if asset_id:
        query += " AND asset_id = ?"
        params.append(asset_id)

    if metric_name:
        query += " AND metric_name = ?"
        params.append(metric_name)

    if start_time:
        query += " AND recorded_at >= ?"
        params.append(start_time)

    if end_time:
        query += " AND recorded_at <= ?"
        params.append(end_time)

    query += " ORDER BY recorded_at DESC LIMIT ?"
    params.append(limit)

    async with db.execute(query, params) as cursor:
        rows = await cursor.fetchall()
        return [dict(row) for row in rows]
