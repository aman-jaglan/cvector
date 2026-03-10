/**
 * Hook for fetching sensor readings and transforming them into
 * chart-ready data grouped by asset name.
 */

import { useCallback } from "react";
import { fetchFacilityDetail, fetchSensorReadings } from "../api/client";
import type { ChartDataPoint, MetricName } from "../types";
import { usePolling } from "./usePolling";

interface SensorChartData {
  chartData: ChartDataPoint[];
  assetNames: string[];
}

export function useSensorData(
  facilityId: string | null,
  metricName: MetricName
) {
  const fetchFn = useCallback(async (): Promise<SensorChartData | null> => {
    if (!facilityId) return null;

    // Fetch readings and facility detail (for asset names) in parallel
    const [readings, facility] = await Promise.all([
      fetchSensorReadings({ facilityId, metricName, limit: 5000 }),
      fetchFacilityDetail(facilityId),
    ]);

    // Build a map of asset IDs to display names
    const assetNameMap = new Map(
      facility.assets.map((asset) => [asset.id, asset.name])
    );

    // Group readings by timestamp, with each asset as a separate key
    const timeMap = new Map<string, ChartDataPoint>();

    // Readings come newest-first from API, so reverse for chronological order
    for (const reading of [...readings].reverse()) {
      const assetName = assetNameMap.get(reading.asset_id) ?? reading.asset_id;

      if (!timeMap.has(reading.recorded_at)) {
        timeMap.set(reading.recorded_at, { timestamp: reading.recorded_at });
      }
      timeMap.get(reading.recorded_at)![assetName] = reading.value;
    }

    const assetNames = [...new Set(
      readings.map((r) => assetNameMap.get(r.asset_id) ?? r.asset_id)
    )];

    return {
      chartData: [...timeMap.values()],
      assetNames,
    };
  }, [facilityId, metricName]);

  return usePolling<SensorChartData | null>(fetchFn);
}
