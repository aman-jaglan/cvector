/**
 * Hook for real-time sensor data streaming.
 *
 * On mount: recovers missed data from database (last 2 hours).
 * Then: polls the queue every second for new readings.
 * Tracks last_seen_id per facility in localStorage to resume correctly.
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

function getLastSeenId(facilityId: string): number | null {
  const stored = localStorage.getItem(`${LAST_SEEN_ID_KEY}_${facilityId}`);
  return stored ? parseInt(stored, 10) : null;
}

function setLastSeenId(facilityId: string, id: number): void {
  localStorage.setItem(`${LAST_SEEN_ID_KEY}_${facilityId}`, String(id));
}

export function useStreamData(facilityId: string | null): UseStreamDataResult {
  const [readings, setReadings] = useState<SensorReading[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [lastUpdated, setLastUpdated] = useState<Date | null>(null);

  // Store interval ID for cleanup
  const intervalRef = useRef<ReturnType<typeof setInterval> | null>(null);

  // Cleanup function to stop polling
  const stopPolling = useCallback(() => {
    if (intervalRef.current) {
      clearInterval(intervalRef.current);
      intervalRef.current = null;
    }
  }, []);

  // Poll: fetch new readings from queue
  const poll = useCallback(async () => {
    if (!facilityId) return;

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

          // Update last seen ID for this facility
          const maxId = Math.max(...facilityReadings.map((r) => r.id));
          setLastSeenId(facilityId, maxId);
          setLastUpdated(new Date());
        }
      }

      setError(null);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Stream error");
    }
  }, [facilityId]);

  // Start polling function
  const startPolling = useCallback(() => {
    stopPolling();
    intervalRef.current = setInterval(poll, POLLING_INTERVAL_MS);
  }, [poll, stopPolling]);

  // Recovery and polling setup on facility change
  useEffect(() => {
    if (!facilityId) return;

    // Reset state for new facility
    setReadings([]);
    setLoading(true);
    stopPolling();

    // Recover historical data then start polling
    const init = async () => {
      try {
        const recoveredReadings = await fetchRecoveryData({
          facilityId,
          windowHours: 2,
        });

        if (recoveredReadings.length > 0) {
          const sortedReadings = recoveredReadings.sort((a, b) =>
            a.recorded_at.localeCompare(b.recorded_at)
          );

          setReadings(sortedReadings);

          const maxId = Math.max(...sortedReadings.map((r) => r.id));
          setLastSeenId(facilityId, maxId);
        }

        setLastUpdated(new Date());
        setError(null);
      } catch (err) {
        setError(err instanceof Error ? err.message : "Recovery failed");
      } finally {
        setLoading(false);
        // Start polling after recovery completes
        startPolling();
      }
    };

    init();

    // Cleanup on unmount or facility change
    return stopPolling;
  }, [facilityId, startPolling, stopPolling]);

  return { readings, loading, error, lastUpdated };
}
