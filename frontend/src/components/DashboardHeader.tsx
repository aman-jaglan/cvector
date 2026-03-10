/** Page header with title and last-updated timestamp. */

import { Space, Tag, Typography } from "antd";

const { Title, Text } = Typography;

interface DashboardHeaderProps {
  facilityName: string | null;
  lastUpdated: Date | null;
}

function DashboardHeader({ facilityName, lastUpdated }: DashboardHeaderProps) {
  return (
    <div style={{ marginBottom: 24 }}>
      <Title level={3} style={{ marginBottom: 4 }}>
        {facilityName ?? "Industrial Dashboard"}
      </Title>
      <Space>
        <Tag color="green">Live</Tag>
        {lastUpdated && (
          <Text type="secondary">
            Last updated: {lastUpdated.toLocaleTimeString()}
          </Text>
        )}
      </Space>
    </div>
  );
}

export default DashboardHeader;
