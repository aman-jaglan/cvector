/**
 * Hook to transform sensor readings into chart-ready data format.
 * Groups readings by timestamp with each asset as a separate key.
 */

import { useCallback, useEffect, useState } from "react";
import { fetchFacilityDetail } from "../api/client";
import type { ChartDataPoint, MetricName, SensorReading } from "../types";

interface ChartData {
  chartData: ChartDataPoint[];
  assetNames: string[];
}

export function useChartData(
  readings: SensorReading[],
  facilityId: string | null,
  metricName: MetricName
): ChartData {
  const [assetNameMap, setAssetNameMap] = useState<Map<string, string>>(
    new Map()
  );

  // Fetch asset names when facility changes
  const loadAssetNames = useCallback(async () => {
    if (!facilityId) return;

    try {
      const facility = await fetchFacilityDetail(facilityId);
      const nameMap = new Map(
        facility.assets.map((asset) => [asset.id, asset.name])
      );
      setAssetNameMap(nameMap);
    } catch {
      // Keep existing map on error
    }
  }, [facilityId]);

  useEffect(() => {
    loadAssetNames();
  }, [loadAssetNames]);

  // Filter readings for this metric
  const metricReadings = readings.filter((r) => r.metric_name === metricName);

  // Group readings by timestamp, with each asset as a separate key
  const timeMap = new Map<string, ChartDataPoint>();

  for (const reading of metricReadings) {
    const assetName = assetNameMap.get(reading.asset_id) ?? reading.asset_id;

    if (!timeMap.has(reading.recorded_at)) {
      timeMap.set(reading.recorded_at, { timestamp: reading.recorded_at });
    }
    timeMap.get(reading.recorded_at)![assetName] = reading.value;
  }

  // Get unique asset names in consistent order
  const assetNames = [
    ...new Set(
      metricReadings.map(
        (r) => assetNameMap.get(r.asset_id) ?? r.asset_id
      )
    ),
  ];

  // Sort by timestamp
  const chartData = [...timeMap.values()].sort((a, b) =>
    a.timestamp.localeCompare(b.timestamp)
  );

  return { chartData, assetNames };
}
