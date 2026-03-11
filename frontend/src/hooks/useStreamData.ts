/**
 * Hook for real-time sensor data streaming using pub/sub pattern.
 *
 * On mount: recovers missed data from database (since last_seen_id).
 * Then: polls the queue every second for new readings.
 * Tracks last_seen_id in localStorage to resume correctly after refresh.
 */

import { useCallback, useEffect, useRef, useState } from "react";
import { fetchRecoveryData, fetchStreamData } from "../api/client";
import { LAST_SEEN_ID_KEY, POLLING_INTERVAL_MS } from "../config";
import type { SensorReading } from "../types";

interface UseStreamDataResult {
  readings: SensorReading[];
  loading: boolean;
  error: string | null;
  lastUpdated: Date | null;
}

function getLastSeenId(): number | null {
  const stored = localStorage.getItem(LAST_SEEN_ID_KEY);
  return stored ? parseInt(stored, 10) : null;
}

function setLastSeenId(id: number): void {
  localStorage.setItem(LAST_SEEN_ID_KEY, String(id));
}

export function useStreamData(facilityId: string | null): UseStreamDataResult {
  const [readings, setReadings] = useState<SensorReading[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [lastUpdated, setLastUpdated] = useState<Date | null>(null);

  // Track if we've done initial recovery
  const hasRecovered = useRef(false);

  // Recovery: fetch missed data from database on mount
  const recover = useCallback(async () => {
    if (!facilityId) return;

    try {
      const lastId = getLastSeenId();
      const recoveredReadings = await fetchRecoveryData({
        sinceId: lastId ?? undefined,
        facilityId,
        windowHours: 2,
      });

      if (recoveredReadings.length > 0) {
        // Filter to only this facility and sort by time
        const facilityReadings = recoveredReadings
          .filter((r) => r.facility_id === facilityId)
          .sort((a, b) => a.recorded_at.localeCompare(b.recorded_at));

        setReadings(facilityReadings);

        // Update last seen ID
        const maxId = Math.max(...facilityReadings.map((r) => r.id));
        setLastSeenId(maxId);
      }

      setLastUpdated(new Date());
      hasRecovered.current = true;
    } catch (err) {
      setError(err instanceof Error ? err.message : "Recovery failed");
    } finally {
      setLoading(false);
    }
  }, [facilityId]);

  // Poll: fetch new readings from queue
  const poll = useCallback(async () => {
    if (!facilityId || !hasRecovered.current) return;

    try {
      const newReadings = await fetchStreamData();

      if (newReadings.length > 0) {
        // Filter to only this facility
        const facilityReadings = newReadings.filter(
          (r) => r.facility_id === facilityId
        );

        if (facilityReadings.length > 0) {
          setReadings((prev) => {
            // Merge new readings, keeping last 2 hours of data
            const twoHoursAgo = new Date(Date.now() - 2 * 60 * 60 * 1000);
            const cutoffTime = twoHoursAgo.toISOString();

            const merged = [...prev, ...facilityReadings]
              .filter((r) => r.recorded_at >= cutoffTime)
              .sort((a, b) => a.recorded_at.localeCompare(b.recorded_at));

            return merged;
          });

          // Update last seen ID
          const maxId = Math.max(...facilityReadings.map((r) => r.id));
          setLastSeenId(maxId);
          setLastUpdated(new Date());
        }
      }

      setError(null);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Stream error");
    }
  }, [facilityId]);

  // Initial recovery on mount or facility change
  useEffect(() => {
    hasRecovered.current = false;
    setReadings([]);
    setLoading(true);
    recover();
  }, [recover]);

  // Start polling after recovery
  useEffect(() => {
    if (!hasRecovered.current) return;

    const timer = setInterval(poll, POLLING_INTERVAL_MS);
    return () => clearInterval(timer);
  }, [poll]);

  return { readings, loading, error, lastUpdated };
}
