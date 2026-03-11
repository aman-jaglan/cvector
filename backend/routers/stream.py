"""Stream endpoints for real-time sensor data polling.

Provides a pub/sub interface where the dashboard polls for new readings
from the in-memory queue. Includes a recovery endpoint for catching up
on missed data from the database.
"""

from typing import Optional

import aiosqlite
from fastapi import APIRouter, Depends, Query

from backend.dependencies import get_db
from backend.models.sensor import SensorReadingResponse
from backend.queue import sensor_queue, SensorReading

router = APIRouter(prefix="/api/stream", tags=["stream"])


def reading_to_response(reading: SensorReading) -> dict:
    """Convert a queue SensorReading to a response dictionary."""
    return {
        "id": reading.id,
        "asset_id": reading.asset_id,
        "facility_id": reading.facility_id,
        "metric_name": reading.metric_name,
        "value": reading.value,
        "unit": reading.unit,
        "recorded_at": reading.recorded_at,
    }


@router.get("", response_model=list[SensorReadingResponse])
async def poll_stream(
    db: aiosqlite.Connection = Depends(get_db),
) -> list[dict]:
    """Poll the queue for new sensor readings.

    Drains all readings from the queue and persists them to the database.
    Returns the readings to the dashboard for display.

    This implements the subscribe side of the pub/sub pattern.
    """
    readings = sensor_queue.subscribe()

    if not readings:
        return []

    # Persist readings to database asynchronously
    await persist_readings(db, readings)

    return [reading_to_response(r) for r in readings]


@router.get("/recovery", response_model=list[SensorReadingResponse])
async def recover_missed_readings(
    since_id: Optional[int] = Query(None, description="Return readings with ID greater than this"),
    facility_id: Optional[str] = Query(None, description="Filter by facility ID"),
    window_hours: int = Query(2, ge=1, le=24, description="Time window in hours"),
    db: aiosqlite.Connection = Depends(get_db),
) -> list[dict]:
    """Recover readings missed while the dashboard was offline.

    Queries the database for readings since the last seen ID or within
    the specified time window. Used by the dashboard on reconnection
    to catch up on missed data.

    Args:
        since_id: Only return readings with ID greater than this value.
        facility_id: Optional filter for a specific facility.
        window_hours: Maximum time window to look back (default 2 hours).

    Returns:
        List of readings from the database, ordered by recorded_at.
    """
    query = """
        SELECT id, asset_id, facility_id, metric_name, value, unit, recorded_at
        FROM sensor_readings
        WHERE recorded_at >= datetime('now', ? || ' hours')
    """
    params: list = [f"-{window_hours}"]

    if since_id is not None:
        query += " AND id > ?"
        params.append(since_id)

    if facility_id:
        query += " AND facility_id = ?"
        params.append(facility_id)

    query += " ORDER BY recorded_at ASC, id ASC"

    async with db.execute(query, params) as cursor:
        rows = await cursor.fetchall()
        return [dict(row) for row in rows]


@router.get("/status")
async def stream_status() -> dict:
    """Get the current status of the stream queue.

    Returns queue size and health information for monitoring.
    """
    return {
        "queue_size": sensor_queue.size(),
        "is_empty": sensor_queue.is_empty(),
    }


async def persist_readings(
    db: aiosqlite.Connection, readings: list[SensorReading]
) -> None:
    """Persist a batch of readings to the database.

    Called after the dashboard consumes readings from the queue
    to ensure data durability.
    """
    if not readings:
        return

    await db.executemany(
        """
        INSERT INTO sensor_readings
            (asset_id, facility_id, metric_name, value, unit, recorded_at)
        VALUES (?, ?, ?, ?, ?, ?)
        """,
        [
            (r.asset_id, r.facility_id, r.metric_name, r.value, r.unit, r.recorded_at)
            for r in readings
        ],
    )
    await db.commit()
