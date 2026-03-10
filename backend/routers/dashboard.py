"""Dashboard summary endpoint — aggregated plant metrics for at-a-glance monitoring."""

import aiosqlite
from fastapi import APIRouter, Depends, HTTPException

from backend.dependencies import get_db
from backend.models.dashboard import DashboardSummaryResponse, MetricSummary

router = APIRouter(prefix="/api/dashboard", tags=["dashboard"])


@router.get("/summary/{facility_id}", response_model=DashboardSummaryResponse)
async def get_dashboard_summary(
    facility_id: str,
    db: aiosqlite.Connection = Depends(get_db),
):
    """Get aggregated dashboard metrics for a facility.

    Returns the latest, average, min, and max values for each metric
    type, along with asset status counts. Uses the most recent reading
    per asset per metric for the "latest" value, and aggregates across
    all readings in the last 2 hours.
    """
    # Verify facility exists and get its name
    async with db.execute(
        "SELECT id, name FROM facilities WHERE id = ?", (facility_id,)
    ) as cursor:
        facility_row = await cursor.fetchone()

    if not facility_row:
        raise HTTPException(status_code=404, detail="Facility not found")

    # Count assets by status
    async with db.execute(
        "SELECT status, COUNT(*) as count FROM assets WHERE facility_id = ? GROUP BY status",
        (facility_id,),
    ) as cursor:
        status_rows = await cursor.fetchall()

    status_counts = {row["status"]: row["count"] for row in status_rows}
    total_assets = sum(status_counts.values())

    # Aggregate sensor readings per metric over the last 2 hours
    async with db.execute(
        """
        SELECT
            metric_name,
            unit,
            AVG(value) as average_value,
            MIN(value) as min_value,
            MAX(value) as max_value
        FROM sensor_readings
        WHERE facility_id = ?
          AND recorded_at >= datetime('now', '-2 hours')
        GROUP BY metric_name, unit
        """,
        (facility_id,),
    ) as cursor:
        metric_rows = await cursor.fetchall()

    # Get the latest reading for each metric (most recent per metric)
    async with db.execute(
        """
        SELECT metric_name, value as latest_value
        FROM sensor_readings
        WHERE facility_id = ?
          AND id IN (
              SELECT id FROM sensor_readings s2
              WHERE s2.facility_id = sensor_readings.facility_id
                AND s2.metric_name = sensor_readings.metric_name
              ORDER BY s2.recorded_at DESC
              LIMIT 1
          )
        GROUP BY metric_name
        """,
        (facility_id,),
    ) as cursor:
        latest_rows = await cursor.fetchall()

    latest_map = {row["metric_name"]: row["latest_value"] for row in latest_rows}

    # Combine aggregated stats with latest values
    metrics = []
    for row in metric_rows:
        metric_name = row["metric_name"]
        metrics.append(
            MetricSummary(
                metric_name=metric_name,
                latest_value=round(latest_map.get(metric_name, row["average_value"]), 2),
                average_value=round(row["average_value"], 2),
                min_value=round(row["min_value"], 2),
                max_value=round(row["max_value"], 2),
                unit=row["unit"],
            )
        )

    return DashboardSummaryResponse(
        facility_id=facility_id,
        facility_name=facility_row["name"],
        total_assets=total_assets,
        assets_running=status_counts.get("running", 0),
        assets_warning=status_counts.get("warning", 0),
        assets_stopped=status_counts.get("stopped", 0),
        metrics=metrics,
    )
