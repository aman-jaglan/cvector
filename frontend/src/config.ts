/** Application-wide configuration constants. */

export const API_BASE_URL = "http://localhost:8000/api";

/** How often to poll the stream endpoint for new readings (milliseconds) */
export const POLLING_INTERVAL_MS = 1_000;

/** localStorage key for tracking last seen reading ID */
export const LAST_SEEN_ID_KEY = "cvector_last_seen_id";
