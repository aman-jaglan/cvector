import { useEffect, useState } from "react";
import { Alert, Col, Layout, Row, Spin, Typography } from "antd";
import { fetchFacilities } from "./api/client";
import DashboardHeader from "./components/DashboardHeader";
import FacilitySelector from "./components/FacilitySelector";
import MetricCards from "./components/MetricCards";
import PowerConsumptionChart from "./components/PowerConsumptionChart";
import TemperatureChart from "./components/TemperatureChart";
import { useDashboard } from "./hooks/useDashboard";
import { useStreamData } from "./hooks/useStreamData";
import type { Facility } from "./types";

const { Content } = Layout;
const { Text } = Typography;

function App() {
  const [facilities, setFacilities] = useState<Facility[]>([]);
  const [selectedFacilityId, setSelectedFacilityId] = useState<string | null>(null);
  const [facilitiesError, setFacilitiesError] = useState<string | null>(null);

  // Load the facility list once on mount
  useEffect(() => {
    const loadFacilities = async () => {
      try {
        const data = await fetchFacilities();
        setFacilities(data);
        // Auto-select the first facility
        if (data.length > 0) {
          setSelectedFacilityId(data[0].id);
        }
      } catch (err) {
        setFacilitiesError(
          err instanceof Error ? err.message : "Failed to load facilities"
        );
      }
    };

    loadFacilities();
  }, []);

  // Dashboard summary for metric cards
  const { data: summary, loading: summaryLoading, error: summaryError, lastUpdated } = useDashboard(selectedFacilityId);

  // Real-time stream data for charts
  const {
    readings: streamReadings,
    loading: streamLoading,
    error: streamError,
  } = useStreamData(selectedFacilityId);

  return (
    <Layout style={{ minHeight: "100vh", background: "#fff" }}>
      <Content style={{ padding: "24px 32px", maxWidth: 1400, margin: "0 auto", width: "100%" }}>
        {/* Header row: title + facility selector */}
        <Row justify="space-between" align="middle" style={{ marginBottom: 16 }}>
          <Col>
            <DashboardHeader
              facilityName={summary?.facility_name ?? null}
              lastUpdated={lastUpdated}
            />
          </Col>
          <Col>
            <Text type="secondary" style={{ marginRight: 8 }}>
              Facility:
            </Text>
            <FacilitySelector
              facilities={facilities}
              selectedId={selectedFacilityId}
              onSelect={setSelectedFacilityId}
            />
          </Col>
        </Row>

        {/* Error states */}
        {facilitiesError && (
          <Alert
            title="Failed to load facilities"
            description={facilitiesError}
            type="error"
            showIcon
            style={{ marginBottom: 16 }}
          />
        )}
        {summaryError && (
          <Alert
            title="Failed to load dashboard data"
            description={summaryError}
            type="error"
            showIcon
            style={{ marginBottom: 16 }}
          />
        )}
        {streamError && (
          <Alert
            title="Stream connection error"
            description={streamError}
            type="warning"
            showIcon
            style={{ marginBottom: 16 }}
          />
        )}

        {/* Loading state */}
        {summaryLoading && !summary && (
          <div style={{ textAlign: "center", padding: 80 }}>
            <Spin size="large" />
          </div>
        )}

        {/* Dashboard content */}
        {summary && (
          <>
            <MetricCards summary={summary} />

            <Row gutter={[16, 16]}>
              <Col xs={24} xl={12}>
                <PowerConsumptionChart
                  facilityId={selectedFacilityId}
                  readings={streamReadings}
                  loading={streamLoading}
                />
              </Col>
              <Col xs={24} xl={12}>
                <TemperatureChart
                  facilityId={selectedFacilityId}
                  readings={streamReadings}
                  loading={streamLoading}
                />
              </Col>
            </Row>
          </>
        )}
      </Content>
    </Layout>
  );
}

export default App;
