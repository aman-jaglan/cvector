/** Row of statistic cards showing key facility metrics. */

import { Card, Col, Row, Statistic } from "antd";
import type { DashboardSummary } from "../types";

/** Human-readable labels and display config for each metric */
const METRIC_DISPLAY: Record<string, { label: string; precision: number }> = {
  power_consumption: { label: "Total Power Consumption", precision: 1 },
  production_output: { label: "Total Production Output", precision: 1 },
  temperature: { label: "Avg Temperature", precision: 1 },
  pressure: { label: "Avg Pressure", precision: 2 },
};

interface MetricCardsProps {
  summary: DashboardSummary;
}

function MetricCards({ summary }: MetricCardsProps) {
  return (
    <Row gutter={[16, 16]} style={{ marginBottom: 24 }}>
      {/* Asset status overview */}
      <Col xs={24} sm={12} md={6}>
        <Card>
          <Statistic
            title="Assets Running"
            value={summary.assets_running}
            suffix={`/ ${summary.total_assets}`}
          />
        </Card>
      </Col>

      {/* One card per metric from the API */}
      {summary.metrics.map((metric) => {
        const display = METRIC_DISPLAY[metric.metric_name];
        if (!display) return null;

        return (
          <Col xs={24} sm={12} md={6} key={metric.metric_name}>
            <Card>
              <Statistic
                title={display.label}
                value={metric.latest_value}
                precision={display.precision}
                suffix={metric.unit}
              />
            </Card>
          </Col>
        );
      })}
    </Row>
  );
}

export default MetricCards;
