/**
 * Shared TypeScript interfaces matching the backend Pydantic models.
 * Single source of truth for all data shapes used across the frontend.
 */

export interface Facility {
  id: string;
  name: string;
  type: "power_station" | "chemical_plant";
  location: string;
  status: "online" | "offline" | "maintenance";
  created_at: string;
}

export interface Asset {
  id: string;
  facility_id: string;
  name: string;
  type: "turbine" | "boiler" | "reactor" | "compressor" | "pump";
  status: "running" | "stopped" | "warning";
  created_at: string;
}

export interface FacilityDetail extends Facility {
  assets: Asset[];
}

export interface SensorReading {
  id: number;
  asset_id: string;
  facility_id: string;
  metric_name: MetricName;
  value: number;
  unit: string;
  recorded_at: string;
}

export type MetricName =
  | "temperature"
  | "pressure"
  | "power_consumption"
  | "production_output";

export interface MetricSummary {
  metric_name: MetricName;
  latest_value: number;
  average_value: number;
  min_value: number;
  max_value: number;
  unit: string;
}

export interface DashboardSummary {
  facility_id: string;
  facility_name: string;
  total_assets: number;
  assets_running: number;
  assets_warning: number;
  assets_stopped: number;
  metrics: MetricSummary[];
}

/** Shape used by Recharts for time-series chart data points */
export interface ChartDataPoint {
  timestamp: string;
  [assetName: string]: string | number;
}
