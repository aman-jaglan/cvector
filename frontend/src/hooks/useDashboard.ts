/** Hook for fetching the dashboard summary for a given facility. */

import { fetchDashboardSummary } from "../api/client";
import type { DashboardSummary } from "../types";
import { usePolling } from "./usePolling";

export function useDashboard(facilityId: string | null) {
  const fetchFn = () => {
    if (!facilityId) return Promise.resolve(null);
    return fetchDashboardSummary(facilityId);
  };

  return usePolling<DashboardSummary | null>(fetchFn);
}
