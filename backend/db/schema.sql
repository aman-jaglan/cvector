-- Industrial monitoring schema: facilities, assets, and sensor readings

CREATE TABLE IF NOT EXISTS facilities (
    id          TEXT PRIMARY KEY,
    name        TEXT NOT NULL,
    type        TEXT NOT NULL CHECK (type IN ('power_station', 'chemical_plant')),
    location    TEXT NOT NULL,
    status      TEXT NOT NULL DEFAULT 'online' CHECK (status IN ('online', 'offline', 'maintenance')),
    created_at  TEXT NOT NULL DEFAULT (datetime('now'))
);

CREATE TABLE IF NOT EXISTS assets (
    id          TEXT PRIMARY KEY,
    facility_id TEXT NOT NULL REFERENCES facilities(id) ON DELETE CASCADE,
    name        TEXT NOT NULL,
    type        TEXT NOT NULL CHECK (type IN ('turbine', 'boiler', 'reactor', 'compressor', 'pump')),
    status      TEXT NOT NULL DEFAULT 'running' CHECK (status IN ('running', 'stopped', 'warning')),
    created_at  TEXT NOT NULL DEFAULT (datetime('now'))
);

CREATE TABLE IF NOT EXISTS sensor_readings (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    asset_id    TEXT NOT NULL REFERENCES assets(id) ON DELETE CASCADE,
    facility_id TEXT NOT NULL REFERENCES facilities(id) ON DELETE CASCADE,
    metric_name TEXT NOT NULL CHECK (metric_name IN ('temperature', 'pressure', 'power_consumption', 'production_output')),
    value       REAL NOT NULL,
    unit        TEXT NOT NULL,
    recorded_at TEXT NOT NULL
);

-- Optimized indexes for common query patterns
CREATE INDEX IF NOT EXISTS idx_readings_facility_time
    ON sensor_readings (facility_id, recorded_at);

CREATE INDEX IF NOT EXISTS idx_readings_asset_metric_time
    ON sensor_readings (asset_id, metric_name, recorded_at);
