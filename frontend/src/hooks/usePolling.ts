/**
 * Generic polling hook — calls a fetch function on an interval
 * and manages loading/error/data state.
 */

import { useCallback, useEffect, useRef, useState } from "react";
import { POLLING_INTERVAL_MS } from "../config";

interface UsePollingResult<T> {
  data: T | null;
  loading: boolean;
  error: string | null;
  lastUpdated: Date | null;
}

export function usePolling<T>(
  fetchFn: () => Promise<T>,
  intervalMs: number = POLLING_INTERVAL_MS
): UsePollingResult<T> {
  const [data, setData] = useState<T | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [lastUpdated, setLastUpdated] = useState<Date | null>(null);

  // Ref to hold the latest fetchFn so the interval doesn't go stale
  const fetchRef = useRef(fetchFn);
  fetchRef.current = fetchFn;

  const execute = useCallback(async () => {
    try {
      const result = await fetchRef.current();
      setData(result);
      setError(null);
      setLastUpdated(new Date());
    } catch (err) {
      setError(err instanceof Error ? err.message : "Unknown error");
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    execute();
    const timer = setInterval(execute, intervalMs);
    return () => clearInterval(timer);
  }, [execute, intervalMs]);

  return { data, loading, error, lastUpdated };
}
