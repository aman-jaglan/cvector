# Industrial Dashboard

A real-time monitoring dashboard for industrial facilities — power stations and chemical plants. Track sensor data across equipment assets with live-updating charts and aggregated metrics.

## Getting Started

### Prerequisites

- Python 3.11+
- Node.js 18+

### Run

```bash
./start.sh
```

Opens two servers:

- **Dashboard** — http://localhost:5173
- **API Docs** — http://localhost:8000/docs

`Ctrl+C` stops everything.

## What's Inside

### Backend — FastAPI + SQLite

Async REST API serving facility data, sensor readings, and dashboard summaries. SQLite database with aiosqlite for non-blocking queries.

### Frontend — React 19 + Ant Design + Recharts

Single-page dashboard with facility selector, metric cards, and time-series line charts. Data auto-refreshes every 30 seconds.

## Database Schema

Three tables model the industrial monitoring domain:

**facilities** — The plants being monitored (power stations, chemical plants). Tracks name, type, location, and operational status.

**assets** — Equipment within each facility (turbines, boilers, reactors, compressors, pumps). Each asset belongs to one facility.

**sensor_readings** — Time-series data from asset sensors. Four metric types: temperature, pressure, power consumption, and production output. Indexed for fast time-range queries by facility and by asset+metric.

## API

| Method | Path | Description |
|--------|------|-------------|
| GET | `/api/facilities/` | List all facilities |
| GET | `/api/facilities/{id}` | Facility with its assets |
| GET | `/api/sensors/readings` | Sensor readings (filterable by facility, asset, metric, time range) |
| GET | `/api/dashboard/summary/{facility_id}` | Aggregated plant metrics |
| GET | `/api/health` | Health check |

Interactive Swagger docs available at `/docs` when the server is running.

## Project Structure

```
backend/
  main.py              App entry point, CORS, lifecycle
  config.py            Database path, allowed origins
  dependencies.py      Shared FastAPI dependencies
  db/
    schema.sql         Table definitions and indexes
    connection.py      Connection management
    seed.py            Sample data generation
  models/              Pydantic v2 response models
  routers/             Endpoint handlers (facilities, sensors, dashboard)

frontend/src/
  config.ts            API URL, polling interval
  types/index.ts       TypeScript interfaces
  api/client.ts        API client (all fetch calls)
  hooks/               usePolling, useDashboard, useSensorData
  components/          UI components (selector, cards, charts)
  App.tsx              Dashboard layout
```

## Tech Stack

| Layer | Technology |
|-------|-----------|
| Backend | Python, FastAPI, aiosqlite, Pydantic v2 |
| Database | SQLite |
| Frontend | React 19, TypeScript, Ant Design, Recharts |
| Build | Vite |

## License

MIT
