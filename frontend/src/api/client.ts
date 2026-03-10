/**
 * Centralized API client — all backend communication goes through here.
 * No fetch calls should exist outside this file.
 */

import { API_BASE_URL } from "../config";
import type {
  DashboardSummary,
  Facility,
  FacilityDetail,
  SensorReading,
} from "../types";

async function fetchJson<T>(url: string): Promise<T> {
  const response = await fetch(url);
  if (!response.ok) {
    throw new Error(`API error: ${response.status} ${response.statusText}`);
  }
  return response.json() as Promise<T>;
}

export function fetchFacilities(): Promise<Facility[]> {
  return fetchJson<Facility[]>(`${API_BASE_URL}/facilities/`);
}

export function fetchFacilityDetail(facilityId: string): Promise<FacilityDetail> {
  return fetchJson<FacilityDetail>(`${API_BASE_URL}/facilities/${facilityId}`);
}

export function fetchSensorReadings(params: {
  facilityId: string;
  metricName?: string;
  limit?: number;
}): Promise<SensorReading[]> {
  const searchParams = new URLSearchParams();
  searchParams.set("facility_id", params.facilityId);
  if (params.metricName) searchParams.set("metric_name", params.metricName);
  if (params.limit) searchParams.set("limit", String(params.limit));

  return fetchJson<SensorReading[]>(
    `${API_BASE_URL}/sensors/readings?${searchParams.toString()}`
  );
}

export function fetchDashboardSummary(
  facilityId: string
): Promise<DashboardSummary> {
  return fetchJson<DashboardSummary>(
    `${API_BASE_URL}/dashboard/summary/${facilityId}`
  );
}
