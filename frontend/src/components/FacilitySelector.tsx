/** Dropdown to select which facility to monitor. */

import { Select } from "antd";
import type { Facility } from "../types";

interface FacilitySelectorProps {
  facilities: Facility[];
  selectedId: string | null;
  onSelect: (facilityId: string) => void;
}

function FacilitySelector({
  facilities,
  selectedId,
  onSelect,
}: FacilitySelectorProps) {
  const options = facilities.map((facility) => ({
    value: facility.id,
    label: `${facility.name} — ${facility.location}`,
  }));

  return (
    <Select
      value={selectedId ?? undefined}
      onChange={onSelect}
      options={options}
      placeholder="Select a facility"
      style={{ width: 360 }}
      size="large"
    />
  );
}

export default FacilitySelector;
