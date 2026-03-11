/** Power consumption chart — one line per asset over the past 2 hours. */

import { useChartData } from "../hooks/useChartData";
import type { SensorReading } from "../types";
import TimeSeriesChart from "./TimeSeriesChart";

interface PowerConsumptionChartProps {
  facilityId: string | null;
  readings: SensorReading[];
  loading: boolean;
}

function PowerConsumptionChart({
  facilityId,
  readings,
  loading,
}: PowerConsumptionChartProps) {
  const { chartData, assetNames } = useChartData(
    readings,
    facilityId,
    "power_consumption"
  );

  return (
    <TimeSeriesChart
      title="Power Consumption (Past 2 Hours)"
      chartData={chartData}
      assetNames={assetNames}
      unit="MW"
      loading={loading}
    />
  );
}

export default PowerConsumptionChart;
