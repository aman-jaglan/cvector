/**
 * High-performance time-series chart using uPlot.
 * Handles large datasets (7000+ points) with smooth 60fps updates.
 * Renders one line per asset with auto-scaling axes.
 */

import { Card, Spin } from "antd";
import { useMemo, useRef, useEffect, useState } from "react";
import UplotReact from "uplot-react";
import type { Options, AlignedData } from "uplot";
import "uplot/dist/uPlot.min.css";
import type { ChartDataPoint } from "../types";

const LINE_COLORS = ["#1890ff", "#52c41a", "#faad14", "#f5222d", "#722ed1"];

interface TimeSeriesChartProps {
  title: string;
  chartData: ChartDataPoint[];
  assetNames: string[];
  unit: string;
  loading: boolean;
}

/**
 * Convert row-based chart data to uPlot's columnar format.
 * uPlot expects: [[timestamps], [series1Values], [series2Values], ...]
 */
function toUplotData(
  chartData: ChartDataPoint[],
  assetNames: string[]
): AlignedData {
  if (chartData.length === 0 || assetNames.length === 0) {
    return [[], ...assetNames.map(() => [])] as AlignedData;
  }

  // X-axis: timestamps as unix seconds
  const timestamps = chartData.map((point) =>
    Math.floor(new Date(point.timestamp).getTime() / 1000)
  );

  // Y-axis: one array per asset
  const series = assetNames.map((name) =>
    chartData.map((point) => {
      const value = point[name];
      return typeof value === "number" ? value : null;
    })
  );

  return [timestamps, ...series] as AlignedData;
}

/**
 * Format unix timestamp for x-axis display.
 */
function formatAxisTime(ts: number): string {
  const date = new Date(ts * 1000);
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
  const containerRef = useRef<HTMLDivElement>(null);
  const [dimensions, setDimensions] = useState({ width: 800, height: 300 });

  // Responsive sizing
  useEffect(() => {
    const updateDimensions = () => {
      if (containerRef.current) {
        const rect = containerRef.current.getBoundingClientRect();
        setDimensions({
          width: Math.max(rect.width - 20, 400),
          height: 300,
        });
      }
    };

    updateDimensions();
    window.addEventListener("resize", updateDimensions);
    return () => window.removeEventListener("resize", updateDimensions);
  }, []);

  // Convert data to uPlot format
  const uplotData = useMemo(
    () => toUplotData(chartData, assetNames),
    [chartData, assetNames]
  );

  // uPlot configuration
  const options = useMemo((): Options => {
    return {
      width: dimensions.width,
      height: dimensions.height,
      tzDate: (ts) => new Date(ts * 1000),
      scales: {
        x: { time: true },
        y: {
          auto: true,
          range: (_u, min, max) => {
            // Add 5% padding to y-axis
            const padding = (max - min) * 0.05 || 1;
            return [min - padding, max + padding];
          },
        },
      },
      axes: [
        {
          // X-axis (time)
          stroke: "#666",
          grid: { stroke: "#eee", width: 1 },
          ticks: { stroke: "#ccc", width: 1 },
          values: (_, ticks) => ticks.map((ts) => formatAxisTime(ts)),
          space: 60,
          incrs: [60, 300, 600, 900, 1800, 3600], // 1m, 5m, 10m, 15m, 30m, 1h
        },
        {
          // Y-axis
          stroke: "#666",
          grid: { stroke: "#eee", width: 1 },
          ticks: { stroke: "#ccc", width: 1 },
          values: (_, ticks) => ticks.map((v) => v.toFixed(1)),
          label: unit,
          labelSize: 14,
          labelGap: 4,
          size: 60,
        },
      ],
      series: [
        // First series is always X (time)
        {},
        // Dynamic series for each asset
        ...assetNames.map((name, index) => ({
          label: name,
          stroke: LINE_COLORS[index % LINE_COLORS.length],
          width: 2,
          points: { show: false },
        })),
      ],
      legend: {
        show: true,
      },
      cursor: {
        sync: { key: "sensor-charts" },
        drag: { x: false, y: false },
      },
    };
  }, [assetNames, unit, dimensions]);

  const hasData = chartData.length > 0 && assetNames.length > 0;

  return (
    <Card title={title} style={{ marginBottom: 24 }}>
      <div ref={containerRef} style={{ width: "100%", height: 350 }}>
        {loading && !hasData ? (
          <div style={{ textAlign: "center", padding: 60 }}>
            <Spin />
          </div>
        ) : hasData ? (
          <UplotReact options={options} data={uplotData} />
        ) : (
          <div
            style={{
              textAlign: "center",
              padding: 60,
              color: "#999",
            }}
          >
            No data available
          </div>
        )}
      </div>
    </Card>
  );
}

export default TimeSeriesChart;
