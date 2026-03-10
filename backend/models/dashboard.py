"""Pydantic models for dashboard summary responses."""

from pydantic import BaseModel


class MetricSummary(BaseModel):
    """Aggregated values for a single metric across a facility."""

    metric_name: str
    latest_value: float
    average_value: float
    min_value: float
    max_value: float
    unit: str


class DashboardSummaryResponse(BaseModel):
    """Overall plant status with aggregated metrics."""

    facility_id: str
    facility_name: str
    total_assets: int
    assets_running: int
    assets_warning: int
    assets_stopped: int
    metrics: list[MetricSummary]
