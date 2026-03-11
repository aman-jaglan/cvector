/** Temperature chart — one line per asset over the past 2 hours. */

import { useChartData } from "../hooks/useChartData";
import type { SensorReading } from "../types";
import TimeSeriesChart from "./TimeSeriesChart";

interface TemperatureChartProps {
  facilityId: string | null;
  readings: SensorReading[];
  loading: boolean;
}

function TemperatureChart({
  facilityId,
  readings,
  loading,
}: TemperatureChartProps) {
  const { chartData, assetNames } = useChartData(
    readings,
    facilityId,
    "temperature"
  );

  return (
    <TimeSeriesChart
      title="Temperature (Past 2 Hours)"
      chartData={chartData}
      assetNames={assetNames}
      unit="°C"
      loading={loading}
    />
  );
}

export default TemperatureChart;
