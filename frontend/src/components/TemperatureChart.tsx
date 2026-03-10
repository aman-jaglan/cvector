/** Temperature chart — one line per asset over the past 2 hours. */

import { useSensorData } from "../hooks/useSensorData";
import TimeSeriesChart from "./TimeSeriesChart";

interface TemperatureChartProps {
  facilityId: string | null;
}

function TemperatureChart({ facilityId }: TemperatureChartProps) {
  const { data, loading } = useSensorData(facilityId, "temperature");

  return (
    <TimeSeriesChart
      title="Temperature (Past 2 Hours)"
      chartData={data?.chartData ?? []}
      assetNames={data?.assetNames ?? []}
      unit="°C"
      loading={loading}
    />
  );
}

export default TemperatureChart;
