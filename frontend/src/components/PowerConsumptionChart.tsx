/** Power consumption chart — one line per asset over the past 2 hours. */

import { useSensorData } from "../hooks/useSensorData";
import TimeSeriesChart from "./TimeSeriesChart";

interface PowerConsumptionChartProps {
  facilityId: string | null;
}

function PowerConsumptionChart({ facilityId }: PowerConsumptionChartProps) {
  const { data, loading } = useSensorData(facilityId, "power_consumption");

  return (
    <TimeSeriesChart
      title="Power Consumption (Past 2 Hours)"
      chartData={data?.chartData ?? []}
      assetNames={data?.assetNames ?? []}
      unit="MW"
      loading={loading}
    />
  );
}

export default PowerConsumptionChart;
