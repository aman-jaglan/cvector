/**
 * Reusable time-series line chart component.
 * Renders one line per asset, with formatted timestamps on the X-axis.
 */

import { Card, Spin } from "antd";
import {
  CartesianGrid,
  Legend,
  Line,
  LineChart,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from "recharts";
import type { ChartDataPoint } from "../types";

const LINE_COLORS = ["#1890ff", "#52c41a", "#faad14", "#f5222d", "#722ed1"];

interface TimeSeriesChartProps {
  title: string;
  chartData: ChartDataPoint[];
  assetNames: string[];
  unit: string;
  loading: boolean;
}

function formatTime(isoString: string): string {
  const date = new Date(isoString);
  const hours = date.getHours().toString().padStart(2, "0");
  const minutes = date.getMinutes().toString().padStart(2, "0");
  return `${hours}:${minutes}`;
}

function TimeSeriesChart({
  title,
  chartData,
  assetNames,
  unit,
  loading,
}: TimeSeriesChartProps) {
  return (
    <Card title={title} style={{ marginBottom: 24 }}>
      {loading ? (
        <div style={{ textAlign: "center", padding: 60 }}>
          <Spin />
        </div>
      ) : (
        <div style={{ width: "100%", height: 350 }}>
          <ResponsiveContainer width="100%" height="100%">
            <LineChart
              data={chartData}
              margin={{ top: 5, right: 30, left: 10, bottom: 5 }}
            >
              <CartesianGrid strokeDasharray="3 3" />
              <XAxis
                dataKey="timestamp"
                tickFormatter={formatTime}
                tick={{ fontSize: 12 }}
              />
              <YAxis
                tick={{ fontSize: 12 }}
                tickFormatter={(value: number) => `${value}`}
                label={{
                  value: unit,
                  angle: -90,
                  position: "insideLeft",
                  style: { fontSize: 12 },
                }}
              />
              <Tooltip
                labelFormatter={(label: string) => formatTime(label)}
                formatter={(value: number) => [`${value.toFixed(2)} ${unit}`]}
              />
              <Legend />
              {assetNames.map((name, index) => (
                <Line
                  key={name}
                  type="monotone"
                  dataKey={name}
                  stroke={LINE_COLORS[index % LINE_COLORS.length]}
                  dot={false}
                  strokeWidth={2}
                />
              ))}
            </LineChart>
          </ResponsiveContainer>
        </div>
      )}
    </Card>
  );
}

export default TimeSeriesChart;
